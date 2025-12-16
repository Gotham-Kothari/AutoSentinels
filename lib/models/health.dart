class Health {
  final String status;

  Health({required this.status});

  factory Health.fromJson(Map<String, dynamic> json) {
    return Health(status: json['status']);
  }
}
