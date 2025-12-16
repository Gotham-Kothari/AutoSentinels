import 'package:flutter/material.dart';
import '../state/health_controller.dart';
import 'package:provider/provider.dart';

import 'chat_screen.dart';
import 'health_detail_screen.dart';

class HomeScreen extends StatelessWidget {
  final String vin;
  const HomeScreen({super.key, required this.vin});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => HealthController()..loadFaults(vin),
      child: Scaffold(
        appBar: AppBar(
          title: Text("Car Health – $vin"),
          actions: [
            IconButton(
              icon: const Icon(Icons.chat),
              onPressed: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => ChatScreen(vin: vin)),
              ),
            ),
          ],
        ),
        body: Consumer<HealthController>(
          builder: (context, ctrl, _) {
            if (ctrl.loading) {
              return const Center(child: CircularProgressIndicator());
            }
            if (ctrl.error != null) {
              return Center(child: Text("Error: ${ctrl.error}"));
            }
            if (ctrl.faults.isEmpty) {
              return const Center(child: Text("No faults found"));
            }
            return ListView.builder(
              itemCount: ctrl.faults.length,
              itemBuilder: (_, i) {
                final f = ctrl.faults[i];
                return ListTile(
                  leading: const Icon(Icons.warning),
                  title: Text(f.component),
                  subtitle: Text(f.rawPayload.anomalyReason),
                  trailing: Text(
                    f.severity.toUpperCase(),
                    style: TextStyle(
                      color: f.severity == "high" ? Colors.red : Colors.orange,
                    ),
                  ),
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => HealthDetailScreen(fault: f),
                    ),
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }
}
