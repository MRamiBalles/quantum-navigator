# Bibliografía Comentada y Validación Científica

Este documento vincula los módulos de software de **Quantum Navigator v4.0/v5.0** con la literatura científica más reciente (2025-2026). El objetivo es validar que nuestra arquitectura de "Middleware de Orquestación" cumple con los estándares industriales actuales.

---

## 1. Hardware y Arquitectura Física
**Módulo Relacionado:** `ZonedCyclesChart`, `VelocityFidelityChart`

*   **[chiu2025continuous] Continuous operation of a coherent 3,000-qubit system**
    *   **Relevancia:** Valida nuestra implementación de la arquitectura de zonas (Storage, Entanglement, Readout).
    *   **Uso en Simulación:** Justifica los tiempos de reordenamiento de ~20ms y la necesidad de modelos de calentamiento ($\Delta n_{vib}$) en la simulación de átomos neutros.

*   **[bombin2023fusion] Fusion-based quantum computation**
    *   **Relevancia:** Base para las arquitecturas fotónicas y arquitecturas que no dependen de la ejecución secuencial de puertas tradicionales.

## 2. Middleware y Compilación
**Módulo Relacionado:** `router.py`, `compiler.py`

*   **[zou2024lightsabre] LightSABRE: A Lightweight and Enhanced SABRE Algorithm**
    *   **Relevancia:** Justifica nuestra decisión de no reimplementar algoritmos de enrutamiento desde cero, sino orquestar soluciones optimizadas que usan "lookahead" y heurísticas avanzadas para reducir la profundidad del circuito.

## 3. Corrección de Errores (QEC)
**Módulo Relacionado:** `backend/server.py` (Decoder Latency Monitor)

*   **[ziad2025local] Local clustering decoder as a fast and adaptive hardware decoder**
    *   **Relevancia:** Identifica el "Decoder Backlog" como un cuello de botella crítico.
    *   **Uso en Simulación:** Valida nuestra nueva métrica de telemetría `decoder_backlog_ms`. Si la latencia de decodificación > tiempo de ciclo, el procesador falla.

## 4. Quantum Machine Learning (QML)
**Módulo Relacionado:** `strategies/adaptive_threshold.py`

*   **[wang2025limitations] Limitations of Amplitude Encoding on Quantum Classification**
    *   **Relevancia:** Provee la justificación matemática para técnicas de poda como nuestro *Adaptive Threshold Pruning (ATP)*. Demuestra que sin estrategias avanzadas, el "Angle Encoding" es ineficiente para datasets complejos.

## 5. Criptografía Post-Cuántica (PQC)
**Módulo Relacionado:** (Futuro) `PQCResilienceTab`

*   **[nist2024fips204] Module-Lattice-Based Digital Signature Standard (ML-DSA)**
    *   **Relevancia:** Establece el estándar contra el cual debemos comparar la potencia de nuestro hardware simulado.

---

## Nota sobre Hipótesis Teóricas
Las referencias a teorías biológicas (ej. [hameroff2014consciousness]) se mantienen separadas de la arquitectura de ingeniería para preservar el rigor del "Digital Twin". Mientras que la sección de hardware simula dispositivos construidos por humanos, estas teorías exploran la coherencia cuántica en sistemas biológicos.
