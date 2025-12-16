// lib/models/chat_message.dart

enum ChatSender { driver, bot }

class ChatMessage {
  final String id;
  final String text;
  final ChatSender sender;
  final DateTime timestamp;

  ChatMessage({
    required this.id,
    required this.text,
    required this.sender,
    required this.timestamp,
  });

  // ----- JSON serialization for persistence -----

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'text': text,
      'sender': sender.name, // "driver" or "bot"
      'timestamp': timestamp.toIso8601String(),
    };
  }

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      id: json['id'] as String,
      text: json['text'] as String,
      sender: (json['sender'] as String) == 'driver'
          ? ChatSender.driver
          : ChatSender.bot,
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }
}
