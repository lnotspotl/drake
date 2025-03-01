#pragma once

#include <vector>

#include "drake/common/drake_copyable.h"
#include "drake/lcmt_jaco_status.hpp"
#include "drake/manipulation/kinova_jaco/jaco_constants.h"
#include "drake/systems/framework/leaf_system.h"

namespace drake {
namespace manipulation {
namespace kinova_jaco {

/// Handles lcmt_jaco_status messages from a LcmSubscriberSystem.
///
/// Note that this system does not actually subscribe to an LCM channel. To
/// receive the message, the input of this system should be connected to a
/// systems::lcm::LcmSubscriberSystem::Make<lcmt_jaco_status>().
///
/// This system has one abstract-valued input port of type lcmt_jaco_status.
///
/// This system has many vector-valued output ports.  All output ports are of
/// size num_joints + num_fingers.  The ports will output zeros until an input
/// message is received.  Finger velocities will be translated from the values
/// used by the Kinova SDK to values appropriate for the finger joints in the
/// Jaco description (see jaco_constants.h.)
//
/// @system
/// name: JacoStatusReceiver
/// input_ports:
/// - lcmt_jaco_status
/// output_ports:
/// - position
/// - velocity
/// - torque
/// - torque_external
/// - current
/// @endsystem
///
/// @see `lcmt_jaco_status.lcm` for additional documentation.
class JacoStatusReceiver : public systems::LeafSystem<double> {
 public:
  DRAKE_NO_COPY_NO_MOVE_NO_ASSIGN(JacoStatusReceiver)

  JacoStatusReceiver(int num_joints = kJacoDefaultArmNumJoints,
                     int num_fingers = kJacoDefaultArmNumFingers);

  DRAKE_DEPRECATED("2022-08-01", "Use position/velocity output ports instead.")
  const systems::OutputPort<double>& get_state_output_port() const;
  DRAKE_DEPRECATED("2022-08-01", "Use torque_measured output port instead.")
  const systems::OutputPort<double>& get_torque_output_port() const {
    return *torque_measured_output_;
  }

  /// @name Named accessors for this System's input and output ports.
  //@{
  const systems::OutputPort<double>& get_position_measured_output_port() const {
    return *position_measured_output_;
  }
  const systems::OutputPort<double>& get_velocity_measured_output_port() const {
    return *velocity_measured_output_;
  }
  const systems::OutputPort<double>& get_torque_measured_output_port() const {
    return *torque_measured_output_;
  }
  const systems::OutputPort<double>& get_torque_external_output_port() const {
    return *torque_external_output_;
  }
  const systems::OutputPort<double>& get_current_output_port() const {
    return *current_output_;
  }
  //@}

 private:
  void CalcStateOutput(const systems::Context<double>&,
                       systems::BasicVector<double>*) const;
  template <std::vector<double> drake::lcmt_jaco_status::*,
            std::vector<double> drake::lcmt_jaco_status::*,
            int>
  void CalcJointOutput(const systems::Context<double>&,
                       systems::BasicVector<double>*) const;

  const int num_joints_;
  const int num_fingers_;
  const systems::InputPort<double>* message_input_{};
  const systems::OutputPort<double>* state_output_{};
  const systems::OutputPort<double>* position_measured_output_{};
  const systems::OutputPort<double>* velocity_measured_output_{};
  const systems::OutputPort<double>* torque_measured_output_{};
  const systems::OutputPort<double>* torque_external_output_{};
  const systems::OutputPort<double>* current_output_{};
};

}  // namespace kinova_jaco
}  // namespace manipulation
}  // namespace drake
