// lib/state/chat_controller.dart

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';

import '../models/chat_message.dart';
import '../services/api_client.dart';

class ChatController extends ChangeNotifier {
  final ApiClient apiClient = ApiClient();
  final _uuid = const Uuid();

  List<ChatMessage> messages = [];
  bool sending = false;

  String? _currentVin;

  // ---------------------------
  // Storage key per VIN
  // ---------------------------
  String _storageKeyForVin(String vin) => 'chat_history_$vin';

  // ---------------------------
  // Load chat history for VIN
  // ---------------------------
  Future<void> loadHistoryForVin(String vin) async {
    _currentVin = vin;

    final prefs = await SharedPreferences.getInstance();
    final key = _storageKeyForVin(vin);

    final storedList = prefs.getStringList(key);

    if (storedList == null) {
      messages = [];
      notifyListeners();
      return;
    }

    messages = storedList
        .map(
          (jsonStr) =>
              ChatMessage.fromJson(jsonDecode(jsonStr) as Map<String, dynamic>),
        )
        .toList();

    notifyListeners();
  }

  // ---------------------------
  // Save chat history for VIN
  // ---------------------------
  Future<void> _saveHistory() async {
    if (_currentVin == null) return;

    final prefs = await SharedPreferences.getInstance();
    final key = _storageKeyForVin(_currentVin!);

    final encoded = messages.map((m) => jsonEncode(m.toJson())).toList();
    await prefs.setStringList(key, encoded);
  }

  // ---------------------------
  // Send message (driver → bot)
  // ---------------------------
  Future<void> sendMessage(String vin, String text) async {
    if (sending) return;

    // Ensure correct VIN context
    if (_currentVin != vin) {
      await loadHistoryForVin(vin);
    }

    sending = true;

    // DRIVER message
    messages.add(
      ChatMessage(
        id: _uuid.v4(),
        sender: ChatSender.driver,
        text: text,
        timestamp: DateTime.now(),
      ),
    );
    notifyListeners();
    await _saveHistory();

    // BOT reply
    try {
      final response = await apiClient.sendChat(vin, text);

      messages.add(
        ChatMessage(
          id: _uuid.v4(),
          sender: ChatSender.bot,
          text: response.botMessage,
          timestamp: DateTime.now(),
        ),
      );
    } catch (e) {
      messages.add(
        ChatMessage(
          id: _uuid.v4(),
          sender: ChatSender.bot,
          text: "Error: $e",
          timestamp: DateTime.now(),
        ),
      );
    }

    sending = false;
    notifyListeners();
    await _saveHistory();
  }
}
