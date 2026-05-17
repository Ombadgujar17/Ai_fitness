import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import '../services/api_service.dart';

class DetectionScreen extends StatefulWidget {
  final String exercise;
  const DetectionScreen({super.key, required this.exercise});

  @override
  State<DetectionScreen> createState() => _DetectionScreenState();
}

class _DetectionScreenState extends State<DetectionScreen> {
  CameraController? _controller;
  Timer? _timer;
  bool _isProcessing = false;

  // UI State
  int _reps = 0;
  String _posture = "GOOD";
  String _feedback = "Initializing...";
  String _state = "up";
  Uint8List? _annotatedBytes;

  @override
  void initState() {
    super.initState();
    _initCamera();
    ApiService.reset(widget.exercise);
  }

  Future<void> _initCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        setState(() => _feedback = "No camera found.");
        return;
      }
      // Use front camera if available
      final camera = cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );

      _controller = CameraController(
        camera,
        ResolutionPreset.low, // Important: use low res to avoid lag
        enableAudio: false,
      );

      await _controller!.initialize();
      if (!mounted) return;
      setState(() {});

      // Start periodic frame capture - reduced to 100ms for higher FPS (up to 10 fps)
      _timer = Timer.periodic(const Duration(milliseconds: 150), (timer) {
        _captureAndSendFrame();
      });
    } catch (e) {
      setState(() => _feedback = "Camera Error: $e");
    }
  }

  Future<void> _captureAndSendFrame() async {
    if (_isProcessing ||
        _controller == null ||
        !_controller!.value.isInitialized) {
      return;
    }

    try {
      _isProcessing = true;
      final xFile = await _controller!.takePicture();
      final bytes = await xFile.readAsBytes();
      final base64Image = base64Encode(bytes);

      final result = await ApiService.predict(base64Image, widget.exercise);

      if (mounted && result.containsKey('reps')) {
        setState(() {
          _reps = result['reps'] ?? _reps;
          _posture = result['posture'] ?? _posture;
          _feedback = result['feedback'] ?? _feedback;
          _state = result['state'] ?? _state;

          if (result['annotated_image'] != null) {
            _annotatedBytes = base64Decode(result['annotated_image']);
          }
        });
      }
    } catch (e) {
      print("Error sending frame: $e");
    } finally {
      if (mounted) _isProcessing = false;
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('${widget.exercise} Tracker')),
      body: Column(
        children: [
          // Camera Preview
          Expanded(
            flex: 3,
            child: Container(
              color: Colors.black,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  if (_controller != null && _controller!.value.isInitialized)
                    CameraPreview(_controller!),
                  if (_controller == null || !_controller!.value.isInitialized)
                    const Center(child: CircularProgressIndicator()),
                  if (_annotatedBytes != null)
                    Image.memory(
                      _annotatedBytes!,
                      fit: BoxFit.contain,
                      gaplessPlayback:
                          true, // Prevents flickering when updating the image
                    ),
                ],
              ),
            ),
          ),

          // Data Display
          Expanded(
            flex: 2,
            child: Container(
              padding: const EdgeInsets.all(20),
              width: double.infinity,
              color: Colors.grey[900],
              child: Column(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  Text(
                    'REPS: $_reps',
                    style: const TextStyle(
                      fontSize: 40,
                      fontWeight: FontWeight.bold,
                      color: Colors.yellow,
                    ),
                  ),
                  Text(
                    'STATE: ${_state.toUpperCase()}',
                    style: const TextStyle(fontSize: 20, color: Colors.white70),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 20,
                      vertical: 10,
                    ),
                    decoration: BoxDecoration(
                      color: _posture == "GOOD"
                          ? Colors.green.withOpacity(0.2)
                          : Colors.red.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: _posture == "GOOD" ? Colors.green : Colors.red,
                        width: 2,
                      ),
                    ),
                    child: Text(
                      _feedback,
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: _posture == "GOOD"
                            ? Colors.greenAccent
                            : Colors.redAccent,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
