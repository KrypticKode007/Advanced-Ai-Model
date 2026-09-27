from src.actuation import CableProfile, DryRunActuator, GuardedHardwareActuator, SafetyPolicy


class FakeTransport:
    def __init__(self, handshake=True, fault=False):
        self.handshake = handshake
        self._fault = fault
        self.enabled_current = None
        self.disabled = False

    def charger_handshake(self, profile):
        return self.handshake

    def enable_output(self, current_limit):
        self.enabled_current = current_limit

    def disable_output(self):
        self.disabled = True

    def faulted(self):
        return self._fault


def test_dry_run_actuator_never_enables_hardware():
    result = DryRunActuator().apply("continue_monitoring", [3.7] * 4, 25.0)

    assert result.status == "DRY_RUN"


def test_interlock_blocks_non_shutdown_action_for_unsafe_pack():
    result = DryRunActuator().apply("reduce_current", [2.4, 3.7, 3.7, 3.7], 25.0)

    assert result.status == "BLOCKED_BY_INTERLOCK"


def test_shutdown_is_allowed_when_interlock_is_triggered():
    result = DryRunActuator().apply("shutdown_pack", [2.4, 3.7, 3.7, 3.7], 25.0)

    assert result.status == "DRY_RUN"


def test_custom_policy_is_shared_by_interlock():
    actuator = DryRunActuator(SafetyPolicy(minimum_voltage=3.6))

    result = actuator.apply("continue_monitoring", [3.5, 3.7, 3.7, 3.7], 25.0)

    assert result.status == "BLOCKED_BY_INTERLOCK"
    assert "shutdown limit" in result.reason


def test_hardware_actuator_rejects_unknown_cable():
    actuator = GuardedHardwareActuator(FakeTransport(), [])

    result = actuator.connect("unknown")

    assert result.status == "BLOCKED_UNKNOWN_CABLE"


def test_hardware_actuator_requires_handshake_and_explicit_arm():
    profile = CableProfile("lab_24v", 24.0, 2.0, "li-ion")
    actuator = GuardedHardwareActuator(FakeTransport(), [profile])

    connected = actuator.connect("lab_24v")
    blocked = actuator.request_charge([3.7] * 4, 25.0, 1.0)
    armed = actuator.arm("ARM_CHARGER")
    energized = actuator.request_charge([3.7] * 4, 25.0, 1.0)

    assert connected.status == "CONNECTED_NOT_ENERGIZED"
    assert blocked.status == "BLOCKED_NOT_ARMED"
    assert armed.status == "ARMED_NOT_ENERGIZED"
    assert energized.status == "ENERGIZED"


def test_hardware_fault_disables_output_and_disarms():
    profile = CableProfile("lab_24v", 24.0, 2.0, "li-ion")
    transport = FakeTransport(fault=True)
    actuator = GuardedHardwareActuator(transport, [profile])
    actuator.connect("lab_24v")
    actuator.arm("ARM_CHARGER")

    result = actuator.request_charge([3.7] * 4, 25.0, 1.0)

    assert result.status == "BLOCKED_TRANSPORT_FAULT"
    assert transport.disabled is True
    assert actuator.armed is False


def test_hardware_actuator_enforces_cable_voltage_limit():
    profile = CableProfile("low_voltage", 10.0, 2.0, "li-ion")
    actuator = GuardedHardwareActuator(FakeTransport(), [profile])
    actuator.connect("low_voltage")
    actuator.arm("ARM_CHARGER")

    result = actuator.request_charge([3.7] * 4, 25.0, 1.0)

    assert result.status == "BLOCKED_VOLTAGE_LIMIT"