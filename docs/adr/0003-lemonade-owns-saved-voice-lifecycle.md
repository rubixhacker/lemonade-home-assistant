# Lemonade owns the saved-voice lifecycle

Lemonade/OpenMOSS owns saved-voice creation, storage, management, and deletion; Home Assistant only discovers and selects those voices for speech. Even if upstream discovery is unavailable, the integration must not create a parallel reference-sample library: this preserves a single lifecycle owner at the cost of depending on an upstream discovery and invocation contract before exposing saved voices in the native picker.
