import 'package:flutter/material.dart';
import '../models/fault.dart';

class HealthDetailScreen extends StatelessWidget {
  final Fault fault;

  const HealthDetailScreen({super.key, required this.fault});

  @override
  Widget build(BuildContext context) {
    final rp = fault.rawPayload;

    return Scaffold(
      appBar: AppBar(title: Text("Fault – ${fault.component}")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
            Text(
              "Severity: ${fault.severity}",
              style: const TextStyle(fontSize: 18),
            ),
            const SizedBox(height: 8),
            Text("Detected at: ${fault.detectedAt}"),
            const SizedBox(height: 16),
            Text(
              rp.anomalyReason,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const Divider(),
            Text(
              "Telemetry Snapshot:",
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text("Coolant Temp: ${rp.coolantTempC} °C"),
            Text("Coolant Pressure: ${rp.coolantPressureBar} bar"),
            Text("Engine RPM: ${rp.engineRpm}"),
            Text("Vibration Level: ${rp.vibrationLevel}"),
            Text("Battery Voltage: ${rp.batteryVoltage}"),
            Text("Odometer: ${rp.odometerKm} km"),
          ],
        ),
      ),
    );
  }
}
