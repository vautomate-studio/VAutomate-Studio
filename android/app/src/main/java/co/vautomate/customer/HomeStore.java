package co.vautomate.customer;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

final class HomeStore {
    private final SharedPreferences storage;
    static final class Home {
        String id,name,local,remote;
        Home(String id,String name,String local,String remote){this.id=id;this.name=name;this.local=local;this.remote=remote;}
        boolean allows(String origin){return !origin.isEmpty() && (EndpointPolicy.sameOrigin(origin,local) || EndpointPolicy.sameOrigin(origin,remote));}
        String label(String origin){return EndpointPolicy.sameOrigin(origin,local)?"Local":"Remote";}
    }
    HomeStore(Context context){storage=context.getSharedPreferences("vautomate-customer-homes",Context.MODE_PRIVATE);}
    List<Home> all(){List<Home> homes=new ArrayList<>();try{JSONArray array=new JSONArray(storage.getString("homes","[]"));for(int i=0;i<array.length();i++){JSONObject item=array.getJSONObject(i);String local=EndpointPolicy.normalize(item.optString("local")),remote=EndpointPolicy.normalize(item.optString("remote"));if(local.isEmpty()&&remote.isEmpty())continue;homes.add(new Home(item.getString("id"),item.optString("name","My home"),local,remote));}}catch(Exception ignored){}return homes;}
    Home selected(){String id=storage.getString("selected","");List<Home> homes=all();for(Home home:homes)if(home.id.equals(id))return home;return homes.isEmpty()?null:homes.get(0);}
    void save(Home home){try{List<Home> homes=all();boolean exists=false;for(int i=0;i<homes.size();i++)if(homes.get(i).id.equals(home.id)){homes.set(i,home);exists=true;break;}if(!exists)homes.add(home);write(homes);select(home);}catch(Exception e){throw new IllegalStateException("Home settings could not be saved.");}}
    void select(Home home){storage.edit().putString("selected",home.id).commit();}
    void remove(Home home){List<Home> homes=all();homes.removeIf(h->h.id.equals(home.id));write(homes);}
    private void write(List<Home> homes){try{JSONArray array=new JSONArray();for(Home home:homes)array.put(new JSONObject().put("id",home.id).put("name",home.name).put("local",home.local).put("remote",home.remote));if(!storage.edit().putString("homes",array.toString()).commit())throw new Exception();}catch(Exception e){throw new IllegalStateException("Home settings could not be saved.");}}
    Home create(String name,String local,String remote){return new Home(UUID.randomUUID().toString(),name,local,remote);}
}
