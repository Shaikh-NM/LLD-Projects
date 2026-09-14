import java.util.Map;
import java.util.HashMap;

class LFUCache{
    static class Node{
        int key, val, freq;
        Node prev, next;

        Node(int key, int value){
            this.key = key;
            this.val = value;
            this.freq = 1;
        }
    }

    static class DoublyLinkedList{
        Node head, tail;
        int size;

        DoublyLinkedList(){
            head = new Node(-1, -1);
            tail = new Node(-1, -1);

            head.next = tail;
            tail.prev = head;

            size = 0;
        }

        void addNode(Node node){
            Node next = head.next;
            Node prev = head;

            node.next = next;
            node.prev = prev;

            prev.next = node;
            next.prev = node;

            size++;
        }

        void removeNode(Node node){
            Node prev = node.prev;
            Node next = node.next;

            node.prev = null;
            node.next = null;

            prev.next = next;
            next.prev = prev;

            size--;
        }

        Node popTail(){
            if(size == 0){
                return null;
            }

            Node lruNode = tail.prev;
            removeNode(lruNode);
            return lruNode;
        }
    }


    private final int capacity;
    private int minFreq;

    private final Map<Integer, Node> keyToNode;
    private final Map<Integer, DoublyLinkedList> freqToList;

    public LFUCache(int capacity){
        this.capacity = capacity;
        this.minFreq = 0;
        this.keyToNode = new HashMap<>();
        this.freqToList = new HashMap<>();
    }

    private void updateNodeFreq(Node node){
        int oldFreq = node.freq;
        DoublyLinkedList oldList = freqToList.get(oldFreq);
        oldList.removeNode(node);

        if (oldList.size() == 0 && minFreq == oldFreq){
            minFreq++;
        }

        node.freq++;
        freqToList.computeIfAbsent(node.freq, k -> new DoublyLinkedList()).addNode(node);
    }

    public int get(int key){
        if (!keyToNode.containsKey(key)){
            return -1;
        }
        Node node = keyToNode.get(key);
        updateNodeFreq(node);
        return node.val;
    }

    public void put(int key, int value){
        if (capacity <= 0){
            return;
        }

        if(keyToNode.containsKey(key)){
            Node node = keyToNode.get(key);
            node.val = value;
            updateNodeFreq(node);
            return;
        }

        if(keyToNode.size() >= capacity){
            DoublyLinkedList minList = freqToList.get(minFreq);
            Node evicted = minList.popTail();
            keyToNode.remove(evicted.key);
        }

        Node newNode = new Node(key, value);
        keyToNode.put(key, newNode);
        minFreq = 1;
        freqToList.computeIfAbsent(1, k -> new DoublyLinkedList()).addNode(newNode);
    }
}