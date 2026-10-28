package co.vautomate.customer;

import java.net.URI;
import java.util.Locale;

/** Independent native HTTP gate. Unknown paths and all configuration writes fail closed. */
final class StudioReadOnlyPolicy {
    static boolean allows(String url,String method,String origin){
        if(!EndpointPolicy.sameOrigin(url,origin))return false;
        try{
            URI uri=URI.create(url);String path=uri.getRawPath();
            if(path==null||path.contains("%")||path.contains("\\")||path.contains(".."))return false;
            String verb=method.toUpperCase(Locale.ROOT);
            if(path.matches("/auth/(token|login_flow(/[a-zA-Z0-9_-]+)?|providers)"))return verb.equals("GET")||verb.equals("POST")||verb.equals("DELETE");
            if(!verb.equals("GET")&&!verb.equals("HEAD"))return false;
            if(path.startsWith("/vautomate-studio/"))return true;
            return path.matches("/api/($|config$|states(/.*)?$|services$|events$|components$|onboarding$|history(/.*)?$|logbook(/.*)?$|camera_proxy(/.*)?$|camera_proxy_stream(/.*)?$|hls(/.*)?$|stream(/.*)?$)");
        }catch(Exception ignored){return false;}
    }
}
