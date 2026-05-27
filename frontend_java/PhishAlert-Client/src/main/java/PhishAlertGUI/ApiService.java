package PhishAlertGUI;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * ApiService - Handles communication with the Python Flask Backend.
 * Features: Real-time analysis, User Feedback Loop, and History Retrieval.
 */
public class ApiService {

    private static final String BASE_URL = "http://127.0.0.1:5000";
    private static final String ANALYZE_URL = BASE_URL + "/analyze";
    private static final String FEEDBACK_URL = BASE_URL + "/feedback";
    private static final String HISTORY_URL = BASE_URL + "/history"; // נתיב ההיסטוריה

    // Reusable HttpClient for better performance
    private static final HttpClient client = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    /**
     * Sends email data to the Python Backend and returns the AI analysis.
     */
    public static JsonObject analyzeEmail(String sender, String body) throws Exception {
        JsonObject jsonRequest = new JsonObject();
        jsonRequest.addProperty("sender", sender);
        jsonRequest.addProperty("body", body);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(ANALYZE_URL))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonRequest.toString()))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        return JsonParser.parseString(response.body()).getAsJsonObject();
    }

    /**
     * Sends the user's manual correction back to the server.
     */
    public static JsonObject sendFeedback(String sender, String correctLabel) throws Exception {
        JsonObject jsonFeedback = new JsonObject();
        jsonFeedback.addProperty("sender", sender);
        jsonFeedback.addProperty("correct_label", correctLabel);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(FEEDBACK_URL))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonFeedback.toString()))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        return JsonParser.parseString(response.body()).getAsJsonObject();
    }

    /**
     * Fetches the full scan history from the local SQLite database via the Python API.
     * This is the method that was missing and caused the compilation error.
     */
    public static JsonArray getHistory() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(HISTORY_URL))
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            throw new RuntimeException("Failed to fetch history. Server returned: " + response.statusCode());
        }

        return JsonParser.parseString(response.body()).getAsJsonArray();
    }
}