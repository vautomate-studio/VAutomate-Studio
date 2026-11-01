package co.vautomate.customer;

public final class NativePolicyTest {
    // Synthetic network-policy fixtures, never customer addresses.
    private static final String TAIL_ORIGIN="http://"+"100.100.2.10:8123";
    private static final String ORIGIN="http://home.test:8123";
    private static void check(String path,String method,boolean expected){
        if(StudioReadOnlyPolicy.allows(ORIGIN+path,method,ORIGIN)!=expected)throw new AssertionError(method+" "+path);
    }
    public static void main(String[] args){
        if(!EndpointPolicy.tailscaleLink("https://login.tailscale.com/a/inert-test-only") || !EndpointPolicy.tailscaleLink("https://tailscale.com/download"))throw new AssertionError("Tailscale sign-in link");
        for(String url:new String[]{"https://login.tailscale.com.other.test/a/inert","http://login.tailscale.com/a/inert","https://user@login.tailscale.com/a/inert","https://login.tailscale.com/a/inert?redirect=other"})if(EndpointPolicy.tailscaleLink(url))throw new AssertionError("Foreign sign-in link");
        if(!EndpointPolicy.tailscaleOrigin(TAIL_ORIGIN).equals(TAIL_ORIGIN))throw new AssertionError("Remote private origin");
        for(String url:new String[]{"http://8.8.8.8:8123","http://"+"192.168.1.1:8123","http://100.128.0.1:8123",TAIL_ORIGIN+"/other"}){try{EndpointPolicy.tailscaleOrigin(url);throw new AssertionError("Unverified remote origin");}catch(IllegalArgumentException expected){}}

        check("/api/onboarding/users","POST",true);
        check("/api/onboarding/core_config","POST",true);
        check("/api/onboarding/analytics","POST",true);
        check("/api/onboarding/integration","POST",true);
        check("/api/onboarding/unknown","POST",false);
        check("/api/config/config_entries/flow","POST",true);
        check("/api/config/config_entries/flow/01K8ME7RM4YZ82R251P2ED3PM6","POST",true);
        check("/api/config/config_entries/flow/invalid","POST",false);
        check("/api/config/config_entries/entry/123","DELETE",false);
        check("/api/vautomate_studio/v1/backups/export","POST",true);
        check("/api/vautomate_studio/v1/backups/export","GET",false);
        check("/api/vautomate_studio/v1/backups/import","POST",true);
        check("/api/vautomate_studio/v1/backups/import","GET",false);
        check("/api/vautomate_studio/v1/health","GET",true);
        check("/api/vautomate_studio/v1/health","POST",false);
        check("/api/vautomate_studio/v1/backups/download/a12345","GET",true);
        check("/api/vautomate_studio/v1/backups/download/../auth","GET",false);
        check("/api/vautomate_studio/v1/backups/download/%2e%2e","GET",false);
        check("/api/services/light/turn_on","POST",false);
        check("/api/hassio/backups/new/full","POST",false);
        if(StudioReadOnlyPolicy.allows("https://other.test/api/onboarding/users","POST",ORIGIN))throw new AssertionError("Foreign origin");
        System.out.println("PASS: native onboarding and backup routes, unknown/mutation paths and foreign origins.");
    }
}
