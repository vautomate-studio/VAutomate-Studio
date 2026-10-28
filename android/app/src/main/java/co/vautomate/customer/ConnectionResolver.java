package co.vautomate.customer;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.IOException;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.*;
import javax.net.ssl.SSLException;

/** Read-only checks; never send a saved credential or repeat a home-control command. */
final class ConnectionResolver {
    static final class Result { final String origin,detail;final boolean success,bundled;Result(String origin,boolean success,String detail){this(origin,success,detail,false);}Result(String origin,boolean success,String detail,boolean bundled){this.origin=origin;this.success=success;this.detail=detail;this.bundled=bundled;} }
    private final ExecutorService workers=Executors.newFixedThreadPool(3);
    Result probe(String origin) {
        HttpURLConnection connection=null;
        try {
            EndpointPolicy.verifyTransport(origin);
            connection=(HttpURLConnection)new URL(origin+EndpointPolicy.DASHBOARD).openConnection();
            connection.setInstanceFollowRedirects(false);connection.setConnectTimeout(1800);connection.setReadTimeout(3200);connection.setRequestProperty("Accept","text/html");connection.setRequestProperty("Cache-Control","no-cache");
            int status=connection.getResponseCode();if(status==404)return probeHomeServer(origin);if(status!=200)return new Result(origin,false,status==401||status==403?"The server requires another access step.":"Server returned HTTP "+status+".");
            String html;try(InputStream input=connection.getInputStream();ByteArrayOutputStream output=new ByteArrayOutputStream()){byte[] buffer=new byte[8192];int count;while((count=input.read(buffer))!=-1){if(output.size()+count>524288)throw new Exception("Unexpected response");output.write(buffer,0,count);}html=output.toString("UTF-8");}
            if(!html.contains("VAutomate") || !html.contains("app.js") || !html.contains("id=\"content\""))return probeHomeServer(origin);
            return new Result(origin,true,"Ready");
        }catch(SSLException error){return new Result(origin,false,"The HTTPS certificate could not be verified.");}
        catch(java.net.SocketTimeoutException error){return new Result(origin,false,"The server did not respond in time.");}
        catch(java.net.UnknownHostException error){return new Result(origin,false,"The server name could not be resolved.");}
        catch(Exception error){return new Result(origin,false,"Could not reach the home. Check Wi-Fi or your private remote connection.");}
        finally{if(connection!=null)connection.disconnect();}
    }
    private Result probeHomeServer(String origin){HttpURLConnection c=null;try{EndpointPolicy.verifyTransport(origin);c=(HttpURLConnection)new URL(origin+"/auth/providers").openConnection();c.setInstanceFollowRedirects(false);c.setConnectTimeout(1800);c.setReadTimeout(3200);c.setRequestProperty("Accept","application/json");int status=c.getResponseCode();if(status!=200&&status!=400&&status!=401&&status!=403)return new Result(origin,false,"The home server did not offer a supported sign-in endpoint ("+status+").");InputStream body=status>=400?c.getErrorStream():c.getInputStream();if(body==null)return new Result(origin,false,"No home sign-in response.");String text;try(InputStream input=body;ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] buffer=new byte[4096];int n;while((n=input.read(buffer))!=-1){if(out.size()+n>65536)throw new IOException("Unexpected response");out.write(buffer,0,n);}text=out.toString("UTF-8").trim();}boolean providers=status==200&&text.startsWith("{")&&text.contains("\"providers\"")&&text.contains("\"type\"");boolean initial=text.startsWith("{")&&text.contains("\"onboarding_required\"");return providers||initial?new Result(origin,true,initial?"New home ready for owner setup":"Home ready for the built-in VAutomate interface",true):new Result(origin,false,"This address is not a supported home server.");}catch(Exception error){return new Result(origin,false,"Could not verify this home server. Check the address and private connection.");}finally{if(c!=null)c.disconnect();}}
    Result resolve(HomeStore.Home home,String forcedOrigin) {
        if(forcedOrigin!=null&&!forcedOrigin.isEmpty())return probe(forcedOrigin);
        List<String> origins=new ArrayList<>();if(!home.local.isEmpty())origins.add(home.local);if(!home.remote.isEmpty()&&!home.remote.equals(home.local))origins.add(home.remote);
        CompletionService<Result> completed=new ExecutorCompletionService<>(workers);List<Future<Result>> jobs=new ArrayList<>();for(String origin:origins)jobs.add(completed.submit(()->probe(origin)));
        Result remoteReady=null;List<String> errors=new ArrayList<>();long started=System.nanoTime();
        try {
            for(int i=0;i<origins.size();i++) {
                Future<Result> future=completed.poll(6,TimeUnit.SECONDS);if(future==null)break;Result result=future.get();
                if(result.success) {
                    if(result.origin.equals(home.local)||home.local.isEmpty())return result;
                    remoteReady=result;
                    long wait=700-TimeUnit.NANOSECONDS.toMillis(System.nanoTime()-started);
                    if(wait>0){Future<Result> local=completed.poll(wait,TimeUnit.MILLISECONDS);if(local!=null){Result localResult=local.get();if(localResult.success&&localResult.origin.equals(home.local))return localResult;}}
                    return remoteReady;
                }
                errors.add(home.label(result.origin)+": "+result.detail);
            }
            return remoteReady!=null?remoteReady:new Result("",false,String.join("\n",errors));
        }catch(InterruptedException error){Thread.currentThread().interrupt();return new Result("",false,"Connection check was cancelled.");}
        catch(Exception error){return new Result("",false,"The connection check could not finish. Try again.");}
        finally{for(Future<Result> job:jobs)job.cancel(true);}
    }
    void close(){workers.shutdownNow();}
}
