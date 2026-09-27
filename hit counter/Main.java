import java.util.ArrayDeque;
import java.util.Deque;
class HitCounter{
    private final Deque<Integer> hits;

    public HitCounter(){
        this.hits = new ArrayDeque<>();
    }

    public void hit(int timestamp){
        hits.offer(timestamp);
    }

    public int getHits(int timestamp){
        int diff = timestamp-300;
        while (!hits.isEmpty() && hits.peek() <= diff){
            hits.poll();
        }
        return hits.size();
    }
}

public class Main{

}