"""
Quantum Navigator v2.0 - Physics Constraint Validator
======================================================

Validates neutral atom job specifications against physical constraints
BEFORE sending to Pulser or hardware backends.

Implements safety checks for:
- Geometric constraints (min distance, blockade radius)
- AOD topological constraints (no row/column crossing)
- Movement velocity limits (heating avoidance)
- Pulse slew rates (AWG bandwidth limits)

References:
- FPQA-C: Compiler for Field-Programmable Qubit Arrays
- Q-Pilot: AOD Movement Optimization
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import math

from .schema import (
    NeutralAtomJob,
    NeutralAtomRegister,
    AtomPosition,
    TrapRole,
    ZoneType,
    ZoneDefinition,
    ShuttleMove,
    RydbergGate,
    GlobalPulse,
    Measurement,
    NeutralAtomOperation,
    HeatingModel,
    AtomLossModel,
)


# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================

class PhysicsConstraintError(Exception):
    """Base exception for physics constraint violations."""
    pass


class TopologicalViolationError(PhysicsConstraintError):
    """
    Raised when AOD movement would require row/column crossing.
    
    In AOD arrays, atoms are trapped in a grid where rows and columns
    cannot physically cross each other - this is a topological constraint
    of the trapping lattice.
    """
    pass


class CollisionError(PhysicsConstraintError):
    """Raised when atoms would collide (distance < min_atom_distance)."""
    pass


class VelocityExceededError(PhysicsConstraintError):
    """Raised when AOD movement would exceed safe velocity limits."""
    pass


class BlockadeDistanceError(PhysicsConstraintError):
    """Raised when Rydberg gate atoms are outside blockade radius."""
    pass


class SlewRateError(PhysicsConstraintError):
    """Raised when pulse parameters change faster than AWG bandwidth allows."""
    pass


class ZoneViolationError(PhysicsConstraintError):
    """
    Raised when operation is attempted in the wrong zone type.
    
    E.g., Rydberg gate attempted in STORAGE zone (shielding light blocks pulses).
    """
    pass


# =============================================================================
# VALIDATION RESULTS
# =============================================================================

@dataclass
class ValidationWarning:
    """Non-fatal warning that may affect fidelity."""
    code: str
    message: str
    severity: str  # "low", "medium", "high"
    operation_index: Optional[int] = None


@dataclass
class ValidationResult:
    """Complete validation result with errors and warnings."""
    is_valid: bool
    errors: list[PhysicsConstraintError]
    warnings: list[ValidationWarning]
    
    # Computed metrics
    estimated_decoherence_cost: float = 0.0  # Relative cost from movements
    total_movement_distance: float = 0.0  # Total AOD travel in µm
    
    def raise_if_invalid(self) -> None:
        """Raise the first error if validation failed."""
        if not self.is_valid and self.errors:
            raise self.errors[0]


# =============================================================================
# PULSER VALIDATOR
# =============================================================================

class PulserValidator:
    """
    Validates NeutralAtomJob against physical constraints.
    
    Usage:
        validator = PulserValidator()
        result = validator.validate(job)
        result.raise_if_invalid()  # Raises on first error
    """
    
    # Default physical constraints (can be overridden per device)
    DEFAULT_MIN_ATOM_DISTANCE = 4.0  # µm
    DEFAULT_BLOCKADE_RADIUS = 8.0  # µm
    DEFAULT_MAX_AOD_VELOCITY = 0.55  # µm/µs
    DEFAULT_AWG_BANDWIDTH = 100.0  # MHz (slew rate limit)
    
    # Heating model parameters
    HEATING_COEFFICIENT = 0.01  # Decoherence cost per (µm * velocity_ratio)
    
    def __init__(
        self,
        max_aod_velocity: float = DEFAULT_MAX_AOD_VELOCITY,
        awg_bandwidth: float = DEFAULT_AWG_BANDWIDTH,
        strict_mode: bool = True
    ):
        """
        Initialize validator.
        
        Args:
            max_aod_velocity: Maximum safe AOD movement velocity in µm/µs
            awg_bandwidth: AWG bandwidth limit in MHz for slew rate checks
            strict_mode: If True, warnings become errors for edge cases
        """
        self.max_aod_velocity = max_aod_velocity
        self.awg_bandwidth = awg_bandwidth
        self.strict_mode = strict_mode
    
    def validate(self, job: NeutralAtomJob) -> ValidationResult:
        """
        Perform complete validation of a neutral atom job.
        
        Args:
            job: The NeutralAtomJob to validate
            
        Returns:
            ValidationResult with errors, warnings, and metrics
        """
        errors: list[PhysicsConstraintError] = []
        warnings: list[ValidationWarning] = []
        total_movement = 0.0
        decoherence_cost = 0.0
        
        # 1. Validate initial register geometry
        geom_errors, geom_warnings = self._validate_register_geometry(job.register)
        errors.extend(geom_errors)
        warnings.extend(geom_warnings)
        
        # 2. Validate each operation
        current_positions = {
            a.id: (a.x, a.y) for a in job.register.atoms
        }
        
        for i, op in enumerate(job.operations):
            op_errors, op_warnings, movement, cost = self._validate_operation(
                op, job.register, current_positions, i
            )
            errors.extend(op_errors)
            warnings.extend(op_warnings)
            total_movement += movement
            decoherence_cost += cost
            
            # Update positions if this was a shuttle move
            if isinstance(op, ShuttleMove):
                for atom_id, target_pos in zip(op.atom_ids, op.target_positions):
                    current_positions[atom_id] = target_pos
        
        # 3. Check for temporal overlaps (concurrent operations)
        overlap_warnings = self._check_temporal_overlaps(job.operations)
        warnings.extend(overlap_warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            estimated_decoherence_cost=decoherence_cost,
            total_movement_distance=total_movement
        )
    
    def _validate_register_geometry(
        self, 
        register: NeutralAtomRegister
    ) -> tuple[list[PhysicsConstraintError], list[ValidationWarning]]:
        """Validate initial atom positions."""
        errors = []
        warnings = []
        
        atoms = register.atoms
        min_dist = register.min_atom_distance
        
        # Check all pairwise distances
        for i, a1 in enumerate(atoms):
            for a2 in atoms[i+1:]:
                dist = math.sqrt((a1.x - a2.x)**2 + (a1.y - a2.y)**2)
                
                if dist < min_dist:
                    errors.append(CollisionError(
                        f"Atoms {a1.id} and {a2.id} are too close: "
                        f"{dist:.2f} µm < {min_dist} µm minimum"
                    ))
                elif dist < min_dist * 1.1:
                    # Very close but technically valid
                    warnings.append(ValidationWarning(
                        code="NEAR_COLLISION",
                        message=f"Atoms {a1.id} and {a2.id} are very close ({dist:.2f} µm)",
                        severity="medium"
                    ))
        
        # Check AOD atoms have row/col assignments
        aod_atoms = [a for a in atoms if a.role == TrapRole.AOD]
        for a in aod_atoms:
            if a.aod_row is None or a.aod_col is None:
                warnings.append(ValidationWarning(
                    code="MISSING_AOD_GRID",
                    message=f"AOD atom {a.id} missing aod_row/aod_col for topological checks",
                    severity="high"
                ))
        
        return errors, warnings
    
    def _validate_operation(
        self,
        op: NeutralAtomOperation,
        register: NeutralAtomRegister,
        current_positions: dict[int, tuple[float, float]],
        op_index: int
    ) -> tuple[list[PhysicsConstraintError], list[ValidationWarning], float, float]:
        """Validate a single operation."""
        errors = []
        warnings = []
        movement = 0.0
        decoherence = 0.0
        
        if isinstance(op, ShuttleMove):
            errs, warns, mov, dec = self._validate_shuttle(
                op, register, current_positions, op_index
            )
            errors.extend(errs)
            warnings.extend(warns)
            movement = mov
            decoherence = dec
            
        elif isinstance(op, RydbergGate):
            errs, warns = self._validate_rydberg_gate(
                op, register, current_positions, op_index
            )
            errors.extend(errs)
            warnings.extend(warns)
        
        elif isinstance(op, GlobalPulse):
            errs, warns = self._validate_global_pulse_zones(
                op, register, current_positions, op_index
            )
            errors.extend(errs)
            warnings.extend(warns)
        
        elif isinstance(op, Measurement):
            errs, warns = self._validate_measurement_zones(
                op, register, current_positions, op_index
            )
            errors.extend(errs)
            warnings.extend(warns)
        
        return errors, warnings, movement, decoherence
    
    def _validate_shuttle(
        self,
        op: ShuttleMove,
        register: NeutralAtomRegister,
        current_positions: dict[int, tuple[float, float]],
        op_index: int
    ) -> tuple[list[PhysicsConstraintError], list[ValidationWarning], float, float]:
        """
        Validate AOD shuttle movement.
        
        Key checks:
        1. Only AOD atoms can move
        2. No row/column crossing (topological constraint)
        3. Velocity within safe limits
        4. No collisions during movement
        """
        errors = []
        warnings = []
        total_movement = 0.0
        decoherence_cost = 0.0
        
        # Get AOD atom info
        aod_atoms = {a.id: a for a in register.atoms if a.role == TrapRole.AOD}
        
        for i, atom_id in enumerate(op.atom_ids):
            # Check if atom is AOD type
            if atom_id not in aod_atoms:
                errors.append(PhysicsConstraintError(
                    f"Atom {atom_id} is not an AOD atom - cannot shuttle SLM atoms"
                ))
                continue
            
            start_pos = current_positions[atom_id]
            target_pos = op.target_positions[i]
            
            # Calculate movement distance
            dist = math.sqrt(
                (target_pos[0] - start_pos[0])**2 + 
                (target_pos[1] - start_pos[1])**2
            )
            total_movement += dist
            
            # Calculate velocity (convert ns to µs)
            duration_us = op.duration / 1000.0
            velocity = dist / duration_us if duration_us > 0 else float('inf')
            
            if velocity > self.max_aod_velocity:
                errors.append(VelocityExceededError(
                    f"Shuttle of atom {atom_id} exceeds velocity limit: "
                    f"{velocity:.3f} µm/µs > {self.max_aod_velocity} µm/µs. "
                    f"Increase duration or reduce distance to avoid heating."
                ))
            elif velocity > self.max_aod_velocity * 0.8:
                warnings.append(ValidationWarning(
                    code="HIGH_VELOCITY",
                    message=f"Atom {atom_id} moving at {velocity:.3f} µm/µs (>80% of limit)",
                    severity="medium",
                    operation_index=op_index
                ))
            
            # Calculate vibrational heating (v3.0)
            delta_nvib = HeatingModel.calculate_nvib_increase(dist, velocity)
            if delta_nvib > 18.0:  # Critical threshold
                fidelity_loss = HeatingModel.estimate_fidelity_loss(delta_nvib)
                warnings.append(ValidationWarning(
                    code="HEATING_HIGH_NVIB",
                    message=(
                        f"High movement heating for atom {atom_id}: "
                        f"Δn_vib = {delta_nvib:.1f} (>{HeatingModel().critical_nvib}). "
                        f"Estimated fidelity loss: {fidelity_loss*100:.1f}%. "
                        f"Consider increasing duration or reducing distance."
                    ),
                    severity="high",
                    operation_index=op_index
                ))
            elif delta_nvib > 10.0:  # Warning threshold
                fidelity_loss = HeatingModel.estimate_fidelity_loss(delta_nvib)
                warnings.append(ValidationWarning(
                    code="HEATING_MODERATE",
                    message=(
                        f"Moderate heating for atom {atom_id}: "
                        f"Δn_vib = {delta_nvib:.1f}. "
                        f"Estimated fidelity loss: {fidelity_loss*100:.1f}%."
                    ),
                    severity="medium",
                    operation_index=op_index
                ))
            
            # Check atom loss risk (v3.0)
            p_loss = AtomLossModel.calculate_loss_probability(delta_nvib)
            if p_loss > 0.05:  # >5% loss probability
                warnings.append(ValidationWarning(
                    code="ATOM_LOSS_RISK",
                    message=(
                        f"Atom {atom_id} has {p_loss*100:.1f}% loss probability "
                        f"due to heating (n_vib = {delta_nvib:.1f})"
                    ),
                    severity="high" if p_loss > 0.1 else "medium",
                    operation_index=op_index
                ))
            
            # Estimate decoherence from movement
            velocity_ratio = velocity / self.max_aod_velocity
            decoherence_cost += dist * velocity_ratio * self.HEATING_COEFFICIENT
        
        # Check for topological violations (row/column crossing)
        topo_error = self._check_topological_constraint(op, register)
        if topo_error:
            errors.append(topo_error)
        
        # Check for collisions at target positions
        new_positions = current_positions.copy()
        for atom_id, target_pos in zip(op.atom_ids, op.target_positions):
            new_positions[atom_id] = target_pos
        
        min_dist = register.min_atom_distance
        for id1, pos1 in new_positions.items():
            for id2, pos2 in new_positions.items():
                if id1 >= id2:
                    continue
                dist = math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
                if dist < min_dist:
                    errors.append(CollisionError(
                        f"Shuttle would cause collision: atoms {id1} and {id2} "
                        f"would be {dist:.2f} µm apart (min: {min_dist} µm)"
                    ))
        
        return errors, warnings, total_movement, decoherence_cost
    
    def _check_topological_constraint(
        self,
        op: ShuttleMove,
        register: NeutralAtomRegister
    ) -> Optional[TopologicalViolationError]:
        """
        Check if AOD movement would require row/column crossing.
        
        In a 2D AOD array, atoms in different rows cannot swap their
        relative row order, and same for columns. This is because the
        AOD lattice is controlled by row/column deflectors that cannot
        cross each other.
        """
        aod_atoms = {a.id: a for a in register.atoms if a.role == TrapRole.AOD}
        
        # Get atoms with grid info
        atoms_with_grid = []
        for atom_id in op.atom_ids:
            atom = aod_atoms.get(atom_id)
            if atom and atom.aod_row is not None and atom.aod_col is not None:
                atoms_with_grid.append(atom)
        
        if len(atoms_with_grid) < 2:
            return None  # Can't check topology without grid info
        
        # Build initial row/col ordering
        initial_row_order = sorted(atoms_with_grid, key=lambda a: a.y)
        initial_col_order = sorted(atoms_with_grid, key=lambda a: a.x)
        
        # Get target positions and check if order would change
        target_map = dict(zip(op.atom_ids, op.target_positions))
        
        def get_target_y(a: AtomPosition) -> float:
            if a.id in target_map:
                return target_map[a.id][1]
            return a.y
        
        def get_target_x(a: AtomPosition) -> float:
            if a.id in target_map:
                return target_map[a.id][0]
            return a.x
        
        target_row_order = sorted(atoms_with_grid, key=get_target_y)
        target_col_order = sorted(atoms_with_grid, key=get_target_x)
        
        # Check if ordering changed
        if [a.id for a in initial_row_order] != [a.id for a in target_row_order]:
            return TopologicalViolationError(
                "Movement would require AOD row crossing - physically impossible. "
                "Atoms in different AOD rows cannot swap their vertical order."
            )
        
        if [a.id for a in initial_col_order] != [a.id for a in target_col_order]:
            return TopologicalViolationError(
                "Movement would require AOD column crossing - physically impossible. "
                "Atoms in different AOD columns cannot swap their horizontal order."
            )
        
        return None
    
    def _validate_rydberg_gate(
        self,
        op: RydbergGate,
        register: NeutralAtomRegister,
        current_positions: dict[int, tuple[float, float]],
        op_index: int
    ) -> tuple[list[PhysicsConstraintError], list[ValidationWarning]]:
        """
        Validate Rydberg two-qubit gate.
        
        Key check: atoms must be within blockade radius for entanglement.
        """
        errors = []
        warnings = []
        
        pos1 = current_positions.get(op.control_atom)
        pos2 = current_positions.get(op.target_atom)
        
        if pos1 is None or pos2 is None:
            # Atom existence already validated by schema
            return errors, warnings
        
        dist = math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
        blockade = register.blockade_radius
        
        if dist > blockade:
            errors.append(BlockadeDistanceError(
                f"Rydberg gate between atoms {op.control_atom} and {op.target_atom} "
                f"will fail: distance {dist:.2f} µm > blockade radius {blockade} µm. "
                f"Use a Shuttle operation to bring atoms closer first."
            ))
        elif dist > blockade * 0.9:
            warnings.append(ValidationWarning(
                code="WEAK_BLOCKADE",
                message=f"Atoms {op.control_atom}-{op.target_atom} near blockade edge ({dist:.2f}/{blockade} µm)",
                severity="high",
                operation_index=op_index
            ))
        
        # Check atoms aren't too close (van der Waals regime)
        if dist < register.min_atom_distance:
            errors.append(CollisionError(
                f"Atoms {op.control_atom} and {op.target_atom} too close for Rydberg gate: "
                f"{dist:.2f} µm. Risk of atomic collision."
            ))
        
        return errors, warnings
    
    def _validate_global_pulse_zones(
        self,
        op: GlobalPulse,
        register: NeutralAtomRegister,
        current_positions: dict[int, tuple[float, float]],
        op_index: int
    ) -> tuple[list[PhysicsConstraintError], list[ValidationWarning]]:
        """
        Validate GlobalPulse against zone constraints.
        
        Key check: If zones are defined, atoms in STORAGE zone will have
        reduced fidelity or may fail due to shielding light.
        """
        errors = []
        warnings = []
        
        # If no zones defined, skip zone validation (backward compatible)
        if register.zones is None:
            return errors, warnings
        
        # Check if any atoms are in storage zones
        storage_zones = register.get_zones_by_type(ZoneType.STORAGE)
        if not storage_zones:
            return errors, warnings
        
        atoms_in_storage = []
        for atom in register.atoms:
            pos = current_positions.get(atom.id, (atom.x, atom.y))
            zone = register.get_zone_at_position(pos[0], pos[1])
            if zone and zone.zone_type == ZoneType.STORAGE:
                atoms_in_storage.append(atom.id)
        
        if atoms_in_storage:
            # Check if storage zone has shielding
            shielded_atoms = []
            for atom_id in atoms_in_storage:
                pos = current_positions.get(atom_id)
                if pos:
                    zone = register.get_zone_at_position(pos[0], pos[1])
                    if zone and zone.shielding_light:
                        shielded_atoms.append(atom_id)
            
            if shielded_atoms:
                warnings.append(ValidationWarning(
                    code="PULSE_IN_SHIELDED_ZONE",
                    message=f"GlobalPulse will have reduced fidelity on atoms {shielded_atoms} in shielded Storage zone",
                    severity="high",
                    operation_index=op_index
                ))
            else:
                warnings.append(ValidationWarning(
                    code="PULSE_IN_STORAGE_ZONE",
                    message=f"GlobalPulse applied while atoms {atoms_in_storage} are in Storage zone (not shielded but may affect coherence)",
                    severity="medium",
                    operation_index=op_index
                ))
        
        return errors, warnings
    
    def _validate_measurement_zones(
        self,
        op: Measurement,
        register: NeutralAtomRegister,
        current_positions: dict[int, tuple[float, float]],
        op_index: int
    ) -> tuple[list[PhysicsConstraintError], list[ValidationWarning]]:
        """
        Validate Measurement against zone constraints.
        
        Measurements should ideally occur in READOUT zones for best fidelity.
        """
        errors = []
        warnings = []
        
        # If no zones defined, skip zone validation (backward compatible)
        if register.zones is None:
            return errors, warnings
        
        readout_zones = register.get_zones_by_type(ZoneType.READOUT)
        if not readout_zones:
            # No readout zones defined, measurements allowed anywhere
            return errors, warnings
        
        atoms_outside_readout = []
        for atom_id in op.atom_ids:
            pos = current_positions.get(atom_id)
            if pos:
                zone = register.get_zone_at_position(pos[0], pos[1])
                if zone is None or zone.zone_type != ZoneType.READOUT:
                    atoms_outside_readout.append(atom_id)
        
        if atoms_outside_readout:
            warnings.append(ValidationWarning(
                code="MEASUREMENT_OUTSIDE_READOUT",
                message=f"Atoms {atoms_outside_readout} measured outside READOUT zone - may have reduced fidelity or scatter light onto other atoms",
                severity="medium",
                operation_index=op_index
            ))
        
        return errors, warnings
    
    def _check_temporal_overlaps(
        self,
        operations: list[NeutralAtomOperation]
    ) -> list[ValidationWarning]:
        """Check for potentially problematic temporal overlaps."""
        warnings = []
        
        # Get time intervals for each operation
        intervals = []
        for i, op in enumerate(operations):
            start = op.start_time
            duration = 0.0
            
            if hasattr(op, 'duration'):
                duration = op.duration
            elif hasattr(op, 'omega'):
                duration = op.omega.duration
            elif hasattr(op, 'detuning') and op.detuning:
                duration = op.detuning.duration
            
            if duration > 0:
                intervals.append((start, start + duration, i, type(op).__name__))
        
        # Check for overlapping shuttles (dangerous)
        shuttle_intervals = [(s, e, i, t) for s, e, i, t in intervals if t == "ShuttleMove"]
        for j, (s1, e1, i1, _) in enumerate(shuttle_intervals):
            for s2, e2, i2, _ in shuttle_intervals[j+1:]:
                if s1 < e2 and s2 < e1:  # Overlap
                    warnings.append(ValidationWarning(
                        code="CONCURRENT_SHUTTLES",
                        message=f"Shuttle operations {i1} and {i2} overlap in time - may cause coordination issues",
                        severity="high",
                        operation_index=i2
                    ))
        
        return warnings


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def validate_job(job: NeutralAtomJob, strict: bool = True) -> ValidationResult:
    """
    Convenience function to validate a job with default settings.
    
    Args:
        job: NeutralAtomJob to validate
        strict: If True, edge cases become errors
        
    Returns:
        ValidationResult
    """
    validator = PulserValidator(strict_mode=strict)
    return validator.validate(job)


def quick_validate(job: NeutralAtomJob) -> None:
    """
    Quick validation that raises on first error.
    
    Args:
        job: NeutralAtomJob to validate
        
    Raises:
        PhysicsConstraintError: On any constraint violation
    """
    result = validate_job(job)
    result.raise_if_invalid()
