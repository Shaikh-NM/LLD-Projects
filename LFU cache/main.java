class LFUCache{
    static class Node{
        int key, value, freq;
        Node prev, next;

        Node(int key, int value){
            this.key = key;
            this.value = value;

            this. freq = 1

            this.prev = this.next = null;
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

        public void addNode(Node node){
            Node prev = head;
            Node next = head.next;

            node.prev = prev;
            node.next = next;

            prev.next = node;
            next.prev = node;

            size++;
        }

        public void removeNode(Node node){
            Node prev = node.prev;
            Node next = node.next;

            prev.next = next;
            next.prev = prev;

            node.prev = null;
            node.next = null;

            size--;
        }

        public Node popTail(){
            if (size == 0){
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

    LFUCache(int capacity){
        this.capacity = capacity;
        this.minFreq = 0

        this.keyToNode = new HashMap<>();
        this.freqToList = new HashMap<>();
    }

    public void updateNodeFreq(Node node){
        int oldFreq = node.freq;
        DoublyLinkedList oldFreqList = freqToList.get(oldFreq);
        oldFreqList.removeNode(node);

        if (oldFreqList.size() == 0 && oldFreq == minFreq){
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
        return node.value;
    }

    public void put(int key, int value){
        if (capacity <= 0){
            return;
        }

        if (keyToNode.containsKey(key)){
            Node node = keyToNode.get(key);
            node.value = value;
            updateNodeFreq(node);
            return;
        }
        if(keyToNode.size() >= capacity){
            DoublyLinkedList minFreqList = freqToList.get(minFreq);
            Node lruNode = minFreqList.popTail();
            keyToNode.remove(lruNode.key);
        }

        Node newNode = new Node(key, value);
        keyToNode.put(key, newNode);
        minFreq = 1;
        freqToList.computeIfAbsent(newNode.freq, k -> new DoublyLinkedList()).addNode(newNode);
    }
}

public class Main{

    public static void main(String[] args){

    }
}