package co.vautomate.customer;

import java.net.IDN;
import java.net.InetAddress;
import java.net.URI;
import java.util.Locale;

/** No credentials, paths, queries or implicit HTTP to public internet in saved origins. */
public final class EndpointPolicy {
    public static final String DASHBOARD = "/vautomate-studio/index.html";
    private EndpointPolicy() {}
    public static String normalize(String value) {
        String text = value == null ? "" : value.trim();
        if (text.isEmpty()) return "";
        if (!text.contains("://")) text = "http://" + text;
        try {
            URI u = new URI(text);
            String scheme = u.getScheme().toLowerCase(Locale.ROOT);
            if (!scheme.equals("http") && !scheme.equals("https")) throw new Exception();
            if (u.getRawUserInfo() != null || u.getRawQuery() != null || u.getRawFragment() != null) throw new Exception();
            String host = u.getHost();
            if (host == null || host.isEmpty() || host.indexOf('%') >= 0) throw new Exception();
            if (!u.getPath().isEmpty() && !u.getPath().equals("/")) throw new Exception();
            int port = u.getPort();
            if (port == 0 || port < -1 || port > 65535) throw new Exception();
            host = host.toLowerCase(Locale.ROOT);
            if (!host.contains(":")) host = IDN.toASCII(host);
            if (host.equals("localhost") || host.startsWith("127.")) throw new Exception();
            if (scheme.equals("http") && host.matches("[0-9.]+") && !privateV4(host))
                throw new IllegalArgumentException("Use HTTPS for a public server address. HTTP is supported for private home and Tailscale addresses.");
            return new URI(scheme, null, host, port, null, null, null).toASCIIString();
        } catch (IllegalArgumentException e) { throw e; }
        catch (Exception e) { throw new IllegalArgumentException("Enter a server address such as http://homeassistant.local:8123, without a dashboard path, password or query."); }
    }
    public static String origin(String url) {
        try { URI u = URI.create(url); return normalize(new URI(u.getScheme(),null,u.getHost(),u.getPort(),null,null,null).toString()); }
        catch (Exception e) { return ""; }
    }
    public static boolean sameOrigin(String first, String second) {
        try {
            URI a = URI.create(first), b = URI.create(second);
            return a.getScheme().equalsIgnoreCase(b.getScheme()) && a.getHost().equalsIgnoreCase(b.getHost()) && effectivePort(a)==effectivePort(b);
        } catch (Exception e) { return false; }
    }
    private static int effectivePort(URI u) { return u.getPort()>=0?u.getPort():"https".equalsIgnoreCase(u.getScheme())?443:80; }
    public static boolean dashboard(String url, String expectedOrigin) {
        try { String path=URI.create(url).getPath();return sameOrigin(url,expectedOrigin) && (path.equals(DASHBOARD) || path.startsWith("/vautomate-studio/")); }
        catch(Exception e) { return false; }
    }
    public static boolean privateV4(String host) {
        String[] parts=host.split("\\."); if(parts.length!=4)return false;int[] n=new int[4];
        try{for(int i=0;i<4;i++){if(parts[i].isEmpty() || (parts[i].length()>1&&parts[i].startsWith("0")))return false;n[i]=Integer.parseInt(parts[i]);if(n[i]<0||n[i]>255)return false;}}catch(Exception e){return false;}
        return n[0]==10 || n[0]==192&&n[1]==168 || n[0]==172&&n[1]>=16&&n[1]<=31 || n[0]==100&&n[1]>=64&&n[1]<=127;
    }
    /** Run before HTTP probes. Certificates on HTTPS always use Android's normal validation. */
    public static void verifyTransport(String origin) throws Exception {
        URI uri=URI.create(origin);if(!"http".equals(uri.getScheme()))return;
        InetAddress[] addresses=InetAddress.getAllByName(uri.getHost());
        if(addresses.length==0)throw new Exception("Server address could not be resolved.");
        for(InetAddress address:addresses) {
            byte[] bytes=address.getAddress();boolean privateAddress=address.isSiteLocalAddress() || address.isLinkLocalAddress() || privateV4(address.getHostAddress()) || bytes.length==16&&(bytes[0]&0xfe)==0xfc;
            if(address.isLoopbackAddress() || !privateAddress)throw new Exception("HTTP is limited to private home or Tailscale addresses. Use HTTPS for public servers.");
        }
    }
}
