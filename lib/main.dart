import 'package:flutter/material.dart';
import 'screens/splash_screen.dart';

void main() {
  runApp(const AutoSentinelsApp());
}

class AutoSentinelsApp extends StatelessWidget {
  const AutoSentinelsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AutoSentinels Driver App',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueGrey),
      ),
      home: const SplashScreen(),
    );
  }
}
