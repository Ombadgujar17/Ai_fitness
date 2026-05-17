import 'package:flutter/material.dart';
import 'detection_screen.dart';

class ExerciseScreen extends StatelessWidget {
  const ExerciseScreen({super.key});

  void _navigateToDetection(BuildContext context, String exerciseName) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => DetectionScreen(exercise: exerciseName),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final exercises = ['Squat', 'Bicep', 'Shoulder'];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Select Exercise'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            const Text(
              'Choose your workout:',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 30),
            Expanded(
              child: ListView.builder(
                itemCount: exercises.length,
                itemBuilder: (context, index) {
                  return Card(
                    margin: const EdgeInsets.symmetric(vertical: 10),
                    child: ListTile(
                      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                      title: Text(
                        exercises[index],
                        style: const TextStyle(fontSize: 18),
                      ),
                      trailing: const Icon(Icons.arrow_forward_ios),
                      onTap: () => _navigateToDetection(context, exercises[index]),
                    ),
                  );
                },
              ),
            )
          ],
        ),
      ),
    );
  }
}
