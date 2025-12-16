import 'package:flutter/material.dart';
import 'home_screen.dart';

class VinSelectScreen extends StatefulWidget {
  const VinSelectScreen({super.key});

  @override
  State<VinSelectScreen> createState() => _VinSelectScreenState();
}

class _VinSelectScreenState extends State<VinSelectScreen> {
  final vinController = TextEditingController(text: "FAULTVIN9999999999999");

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Enter VIN")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: vinController,
              decoration: const InputDecoration(
                labelText: "VIN",
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => HomeScreen(vin: vinController.text),
                  ),
                );
              },
              child: const Text("Continue"),
            ),
          ],
        ),
      ),
    );
  }
}
