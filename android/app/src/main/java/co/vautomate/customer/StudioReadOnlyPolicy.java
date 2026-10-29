package co.vautomate.customer;

import java.net.URI;
import java.util.Locale;

/** Independent native HTTP gate. Only authentication, known setup and Studio routes may write. */
final class StudioReadOnlyPolicy {
    static boolean allows(String url,String method,String origin){
        if(!EndpointPolicy.sameOrigin(url,origin))return false;
        try{
            URI uri=URI.create(url);String path=uri.getRawPath();
            if(path==null||path.contains("%")||path.contains("\\")||path.contains(".."))return false;
            String verb=method.toUpperCase(Locale.ROOT);
            if(path.matches("/auth/(token|login_flow(/[a-zA-Z0-9_-]+)?|providers)"))return verb.equals("GET")||verb.equals("POST")||verb.equals("DELETE");
            if(path.matches("/api/onboarding/(users|core_config|analytics|integration)"))return verb.equals("POST");
            if(path.matches("/api/config/config_entries/flow(/([a-f0-9]{32}|[0-9A-HJKMNP-TV-Z]{26}))?"))return verb.equals("POST");
            if(path.matches("/api/vautomate_studio/v1/backups/(export|import)"))return verb.equals("POST");
            if(path.equals("/api/vautomate_studio/v1/health"))return verb.equals("GET");
            if(path.matches("/api/vautomate_studio/v1/backups/download/[A-Za-z0-9_-]{1,128}"))return verb.equals("GET")||verb.equals("HEAD");
            if(!verb.equals("GET")&&!verb.equals("HEAD"))return false;
            if(path.startsWith("/vautomate-studio/"))return true;
            return path.matches("/api/($|config$|states(/.*)?$|services$|events$|components$|onboarding$|history(/.*)?$|logbook(/.*)?$|camera_proxy(/.*)?$|camera_proxy_stream(/.*)?$|hls(/.*)?$|stream(/.*)?$)");
        }catch(Exception ignored){return false;}
    }
}
