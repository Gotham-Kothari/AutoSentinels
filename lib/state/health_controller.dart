import 'package:flutter/material.dart';
import '../models/fault.dart';
import '../services/api_client.dart';

class HealthController extends ChangeNotifier {
  final ApiClient apiClient = ApiClient();

  List<Fault> faults = [];
  bool loading = false;
  String? error;

  Future<void> loadFaults(String vin) async {
    loading = true;
    error = null;
    notifyListeners();

    try {
      faults = await apiClient.getFaultsForVin(vin);
    } catch (e) {
      error = e.toString();
    }

    loading = false;
    notifyListeners();
  }
}
