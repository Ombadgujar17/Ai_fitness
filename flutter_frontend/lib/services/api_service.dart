import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // Use localhost for local development
  static const String baseUrl = 'http://127.0.0.1:8000';

  static Future<Map<String, dynamic>> predict(String base64Image, String exercise) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/predict'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'image': base64Image,
          'exercise': exercise,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        return {'error': 'Server error: ${response.statusCode}'};
      }
    } catch (e) {
      return {'error': 'Failed to connect: $e'};
    }
  }

  static Future<void> reset(String exercise) async {
    try {
      await http.post(Uri.parse('$baseUrl/reset?exercise=$exercise'));
    } catch (e) {
      print('Failed to reset: $e');
    }
  }
}
