import java.util.HashMap;
import java.util.Map;
import java.util.TreeSet;

class FoodRatings {
    private static class FoodItem implements Comparable<FoodItem> {
        String name;
        int rating;

        FoodItem(String name, int rating) {
            this.name = name;
            this.rating = rating;
        }

        @Override
        public int compareTo(FoodItem other) {
            if (this.rating != other.rating) {
                return Integer.compare(other.rating, this.rating);
            }
            return this.name.compareTo(other.name);
        }
    }

    private final Map<String, String> foodToCuisine;
    private final Map<String, FoodItem> foodToItem;
    private final Map<String, TreeSet<FoodItem>> cuisineMap;

    public FoodRatings(String[] foods, String[] cuisines, int[] ratings) {
        foodToCuisine = new HashMap<>();
        foodToItem = new HashMap<>();
        cuisineMap = new HashMap<>();

        for (int i = 0; i < foods.length; i++) {
            String food = foods[i];
            String cuisine = cuisines[i];
            int rating = ratings[i];

            FoodItem item = new FoodItem(food, rating);
            foodToCuisine.put(food, cuisine);
            foodToItem.put(food, item);

            cuisineMap.computeIfAbsent(cuisine, k -> new TreeSet<>()).add(item);
        }
    }

    public void changeRating(String food, int newRating) {
        String cuisine = foodToCuisine.get(food);
        TreeSet<FoodItem> set = cuisineMap.get(cuisine);

        FoodItem oldItem = foodToItem.get(food);
        set.remove(oldItem);

        FoodItem updatedItem = new FoodItem(food, newRating);
        set.add(updatedItem);
        foodToItem.put(food, updatedItem);
    }

    public String highestRated(String cuisine) {
        return cuisineMap.get(cuisine).first().name;
    }
}