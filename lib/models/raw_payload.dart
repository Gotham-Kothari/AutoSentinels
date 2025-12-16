class RawPayload {
  final String vin;
  final String timestamp;
  final double coolantTempC;
  final double coolantPressureBar;
  final int engineRpm;
  final int vibrationLevel;
  final double batteryVoltage;
  final double odometerKm;
  final String anomalyReason;
  final double predictedFailureKm;
  final String component;
  final String severity;

  RawPayload({
    required this.vin,
    required this.timestamp,
    required this.coolantTempC,
    required this.coolantPressureBar,
    required this.engineRpm,
    required this.vibrationLevel,
    required this.batteryVoltage,
    required this.odometerKm,
    required this.anomalyReason,
    required this.predictedFailureKm,
    required this.component,
    required this.severity,
  });

  factory RawPayload.fromJson(Map<String, dynamic> json) {
    return RawPayload(
      vin: json['vin'] as String,
      timestamp: json['timestamp'] as String,
      coolantTempC: (json['coolant_temp_c'] as num).toDouble(),
      coolantPressureBar: (json['coolant_pressure_bar'] as num).toDouble(),
      engineRpm: (json['engine_rpm'] as num).toInt(),
      vibrationLevel: (json['vibration_level'] as num).toInt(),
      batteryVoltage: (json['battery_voltage'] as num).toDouble(),
      odometerKm: (json['odometer_km'] as num).toDouble(),
      anomalyReason: json['anomaly_reason'] as String,
      predictedFailureKm: (json['predicted_failure_km'] as num).toDouble(),
      component: json['component'] as String,
      severity: json['severity'] as String,
    );
  }
}
