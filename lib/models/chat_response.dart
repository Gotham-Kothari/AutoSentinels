class ChatResponse {
  final String botMessage;

  ChatResponse({required this.botMessage});

  factory ChatResponse.fromJson(Map<String, dynamic> json) {
    return ChatResponse(botMessage: json['bot_message']);
  }
}
