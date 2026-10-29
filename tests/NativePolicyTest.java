package co.vautomate.customer;

public final class NativePolicyTest {
    private static final String ORIGIN="http://home.test:8123";
    private static void check(String path,String method,boolean expected){
        if(StudioReadOnlyPolicy.allows(ORIGIN+path,method,ORIGIN)!=expected)throw new AssertionError(method+" "+path);
    }
    public static void main(String[] args){
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
        check("/api/vautomate_studio/v1/backups/download/a12345","GET",true);
        check("/api/vautomate_studio/v1/backups/download/../auth","GET",false);
        check("/api/vautomate_studio/v1/backups/download/%2e%2e","GET",false);
        check("/api/services/light/turn_on","POST",false);
        check("/api/hassio/backups/new/full","POST",false);
        if(StudioReadOnlyPolicy.allows("https://other.test/api/onboarding/users","POST",ORIGIN))throw new AssertionError("Foreign origin");
        System.out.println("PASS: native onboarding and backup routes, unknown/mutation paths and foreign origins.");
    }
}
