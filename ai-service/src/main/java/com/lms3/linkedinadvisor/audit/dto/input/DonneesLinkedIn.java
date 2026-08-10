package com.lms3.linkedinadvisor.audit.dto.input;


import java.util.List;

// ---------- DonneesLinkedIn.java (racine) ----------
public record DonneesLinkedIn(
        Metadata metadata,
        Entreprise entreprise,
        Dirigeant dirigeant
) {}
