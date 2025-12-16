import 'raw_payload.dart';

class Fault {
  final String id;
  final String vin;
  final String detectedAt;
  final double predictedFailureKm;
  final String component;
  final String severity;
  final RawPayload rawPayload;

  Fault({
    required this.id,
    required this.vin,
    required this.detectedAt,
    required this.predictedFailureKm,
    required this.component,
    required this.severity,
    required this.rawPayload,
  });

  factory Fault.fromJson(Map<String, dynamic> json) {
    return Fault(
      id: json['id'],
      vin: json['vin'],
      detectedAt: json['detected_at'],
      predictedFailureKm: (json['predicted_failure_km'] as num).toDouble(),
      component: json['component'],
      severity: json['severity'],
      rawPayload: RawPayload.fromJson(json['raw_payload']),
    );
  }
}
