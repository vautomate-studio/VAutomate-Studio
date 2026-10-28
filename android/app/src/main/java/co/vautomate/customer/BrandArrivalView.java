package co.vautomate.customer;

import android.content.Context;
import android.graphics.*;
import android.os.SystemClock;
import android.view.View;

/** A self-contained logo animation. Its clock starts on the first painted frame. */
final class BrandArrivalView extends View {
    static final long DURATION=3200;
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path left=BrandPaths.mark0(),right=BrandPaths.mark1(),wordmark=BrandPaths.wordmark();
    private final boolean motion=android.animation.ValueAnimator.areAnimatorsEnabled();
    private final float density;
    private final String connection;
    private long started=-1;
    private Runnable completion;
    private boolean complete;
    BrandArrivalView(Context context,String connection){super(context);this.connection=connection;density=getResources().getDisplayMetrics().density;setContentDescription("VAutomate. Smart living. Simplified.");setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_YES);}
    void whenComplete(Runnable callback){if(complete)post(callback);else completion=callback;}
    private float phase(float time,float from,float to){return Math.max(0,Math.min(1,(time-from)/(to-from)));}
    private float ease(float value){return 1-(float)Math.pow(1-value,3);}
    private void logo(Canvas canvas,Path path,float x,float y,float scale,float alpha,float sweep,float offset){
        canvas.save();canvas.translate(x+offset,y);canvas.scale(scale,scale);paint.setShader(null);paint.setColor(Color.rgb(248,247,240));paint.setAlpha(Math.round(255*alpha));canvas.drawPath(path,paint);
        if(sweep>0&&sweep<1){canvas.clipPath(path);float sx=-95+sweep*410;paint.setShader(new LinearGradient(sx-30,0,sx+30,0,new int[]{0x00FFFFFF,0xAAD9C8A6,0x00FFFFFF},null,Shader.TileMode.CLAMP));paint.setAlpha(Math.round(150*alpha));canvas.drawRect(-100,-20,310,120,paint);paint.setShader(null);}
        canvas.restore();paint.setAlpha(255);
    }
    @Override protected void onDraw(Canvas canvas){
        super.onDraw(canvas);if(started<0)started=SystemClock.uptimeMillis();long elapsed=SystemClock.uptimeMillis()-started;float t=motion?elapsed/1000f:3.2f;
        float cx=getWidth()/2f,cy=getHeight()*.45f,d=density,formation=ease(phase(t,0,.95f)),reveal=ease(phase(t,.7f,1.7f)),signature=ease(phase(t,1.35f,2.15f)),sweep=phase(t,1.65f,2.65f);
        canvas.drawColor(Color.rgb(8,9,11));paint.setShader(new RadialGradient(cx,cy,225*d,new int[]{Color.rgb(33,31,27),Color.rgb(8,9,11)},null,Shader.TileMode.CLAMP));canvas.drawRect(0,0,getWidth(),getHeight(),paint);paint.setShader(null);
        float markScale=Math.min(1.05f*d,getWidth()*.28f/105f),markX=cx-105*markScale/2,markY=cy-86*d;
        logo(canvas,left,markX,markY,markScale,.35f+.65f*formation,sweep,-18*d*(1-formation));logo(canvas,right,markX,markY,markScale,.35f+.65f*formation,sweep,18*d*(1-formation));
        float wordScale=Math.min(1.15f*d,getWidth()*.62f/194f),wordWidth=194*wordScale;
        canvas.save();canvas.clipRect(cx-wordWidth/2*reveal,cy+15*d,cx+wordWidth/2*reveal,cy+70*d);logo(canvas,wordmark,cx-wordWidth/2,cy+24*d+(1-reveal)*9*d,wordScale,reveal,sweep,0);canvas.restore();
        paint.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));paint.setTextSize(8*d);paint.setColor(Color.rgb(203,183,141));paint.setAlpha(Math.round(255*signature));String tagline="SMART LIVING. SIMPLIFIED.";float tracking=2.6f*d,width=paint.measureText(tagline)+(tagline.length()-1)*tracking,x=cx-width/2;for(int i=0;i<tagline.length();i++){String letter=tagline.substring(i,i+1);canvas.drawText(letter,x,cy+100*d,paint);x+=paint.measureText(letter)+tracking;}
        if(elapsed>4200){paint.setAlpha(210);paint.setTextSize(11*d);paint.setColor(Color.rgb(156,158,158));paint.setTextAlign(Paint.Align.CENTER);canvas.drawText(connection,cx,cy+153*d,paint);paint.setTextAlign(Paint.Align.LEFT);}paint.setAlpha(255);
        if(!complete&&elapsed>=(motion?DURATION:450)){complete=true;Runnable callback=completion;completion=null;if(callback!=null)post(callback);}if(!complete)postInvalidateOnAnimation();else if(elapsed<4500)postInvalidateDelayed(600);
    }
    @Override protected void onDetachedFromWindow(){completion=null;super.onDetachedFromWindow();}
}
