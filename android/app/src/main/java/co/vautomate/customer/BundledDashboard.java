package co.vautomate.customer;

import android.content.Context;
import android.net.Uri;
import android.webkit.WebResourceResponse;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Immutable app assets served only within the selected home's dashboard namespace. */
final class BundledDashboard {
    private static final String PREFIX="/vautomate-studio/";
    private final Context context;
    private final Set<String> allowed=new HashSet<>();
    BundledDashboard(Context context)throws IOException{this.context=context;try(BufferedReader reader=new BufferedReader(new InputStreamReader(context.getAssets().open("customer-asset-index.txt"),StandardCharsets.UTF_8))){String line;while((line=reader.readLine())!=null)if(safeRelative(line))allowed.add(line);}if(!allowed.contains("index.html")||!allowed.contains("onboarding.js"))throw new IOException("The customer dashboard is incomplete");}
    static boolean safeRelative(String path){return path!=null&&!path.isEmpty()&&!path.startsWith("/")&&!path.contains("\\")&&!path.contains("%")&&!path.contains("\0")&&Arrays.stream(path.split("/",-1)).noneMatch(part->part.isEmpty()||part.equals(".")||part.equals(".."));}
    String entry()throws IOException{try(InputStream input=context.getAssets().open("vautomate-customer/index.html");ByteArrayOutputStream output=new ByteArrayOutputStream()){byte[] buffer=new byte[8192];int n;while((n=input.read(buffer))!=-1)output.write(buffer,0,n);return output.toString("UTF-8");}}
    WebResourceResponse response(Uri uri){String path=uri.getPath();if(path==null||!path.startsWith(PREFIX))return null;String relative=path.substring(PREFIX.length());if(!safeRelative(relative)||!allowed.contains(relative))return missing();try{String mime=relative.endsWith(".html")?"text/html":relative.endsWith(".js")?"text/javascript":relative.endsWith(".css")?"text/css":relative.endsWith(".svg")?"image/svg+xml":relative.endsWith(".json")?"application/json":relative.endsWith(".woff2")?"font/woff2":relative.endsWith(".woff")?"font/woff":relative.endsWith(".png")?"image/png":relative.endsWith(".jpg")?"image/jpeg":relative.endsWith(".wasm")?"application/wasm":"application/octet-stream";Map<String,String> headers=new HashMap<>();headers.put("Cache-Control","no-store");headers.put("X-Content-Type-Options","nosniff");return new WebResourceResponse(mime,mime.startsWith("text/")||mime.equals("image/svg+xml")||mime.equals("application/json")?"UTF-8":null,200,"OK",headers,context.getAssets().open("vautomate-customer/"+relative));}catch(IOException error){return missing();}}
    private WebResourceResponse missing(){return new WebResourceResponse("text/plain","UTF-8",404,"Not Found",Collections.emptyMap(),new ByteArrayInputStream("VAutomate asset unavailable".getBytes(StandardCharsets.UTF_8)));}
}
