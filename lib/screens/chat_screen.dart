// lib/screens/chat_screen.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/chat_message.dart';
import '../state/chat_controller.dart';

class ChatScreen extends StatelessWidget {
  final String vin;

  const ChatScreen({super.key, required this.vin});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => ChatController(),
      child: _ChatView(vin: vin),
    );
  }
}

class _ChatView extends StatefulWidget {
  final String vin;
  const _ChatView({required this.vin});

  @override
  State<_ChatView> createState() => _ChatViewState();
}

class _ChatViewState extends State<_ChatView> {
  final controller = TextEditingController();

  @override
  void initState() {
    super.initState();
    // Load persisted chat history for this VIN once when screen opens
    Future.microtask(() {
      final chat = Provider.of<ChatController>(context, listen: false);
      chat.loadHistoryForVin(widget.vin);
    });
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final chat = Provider.of<ChatController>(context);

    final reversedMessages = chat.messages.reversed.toList();

    return Scaffold(
      appBar: AppBar(title: Text("Assistant – ${widget.vin}")),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              reverse: true,
              padding: const EdgeInsets.all(12),
              itemCount: reversedMessages.length,
              itemBuilder: (_, i) {
                final msg = reversedMessages[i];
                final isDriver = msg.sender == ChatSender.driver;

                return Align(
                  alignment: isDriver
                      ? Alignment.centerRight
                      : Alignment.centerLeft,
                  child: Container(
                    padding: const EdgeInsets.all(12),
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    decoration: BoxDecoration(
                      color: isDriver ? Colors.blueGrey : Colors.grey.shade200,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      msg.text,
                      style: TextStyle(
                        color: isDriver ? Colors.white : Colors.black,
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: controller,
                    decoration: const InputDecoration(
                      hintText: "Ask about your car health...",
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  icon: chat.sending
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.send),
                  onPressed: chat.sending
                      ? null
                      : () {
                          final text = controller.text.trim();
                          if (text.isNotEmpty) {
                            chat.sendMessage(widget.vin, text);
                            controller.clear();
                          }
                        },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
