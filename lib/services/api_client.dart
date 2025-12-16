import 'dart:convert';
import 'package:http/http.dart' as http;

import '../config.dart';
import '../models/fault.dart';
import '../models/chat_response.dart';
import '../models/health.dart';

class ApiClient {
  final String baseUrl;

  ApiClient({this.baseUrl = kBackendBaseUrl});

  Future<Health> getHealth() async {
    final uri = Uri.parse('$baseUrl/health');
    final response = await http.get(uri);

    if (response.statusCode == 200) {
      return Health.fromJson(jsonDecode(response.body));
    }
    throw Exception('Failed to fetch health');
  }

  Future<List<Fault>> getFaultsForVin(String vin) async {
    // Call the real backend route: /faults
    final uri = Uri.parse('$baseUrl/faults');
    final response = await http.get(uri);

    if (response.statusCode == 200) {
      final list = jsonDecode(response.body) as List<dynamic>;
      final allFaults = list
          .map((e) => Fault.fromJson(e as Map<String, dynamic>))
          .toList();

      // Filter client-side by VIN
      final filtered = allFaults.where((f) => f.vin == vin).toList();

      return filtered;
    } else {
      // Debug logging to console
      print('getFaultsForVin failed: ${response.statusCode}');
      print('Body: ${response.body}');
      throw Exception('Failed to fetch faults');
    }
  }

  Future<ChatResponse> sendChat(String vin, String message) async {
    final uri = Uri.parse('$baseUrl/chat');
    final body = jsonEncode({"vin": vin, "message": message});

    final response = await http.post(
      uri,
      headers: {"Content-Type": "application/json"},
      body: body,
    );

    if (response.statusCode == 200) {
      return ChatResponse.fromJson(jsonDecode(response.body));
    }
    throw Exception('Chat failed');
  }
}
