export type Intent = 
  | 'GET_CURRENT_STATUS'
  | 'GET_INCIDENT'
  | 'GET_RECOMMENDATION'
  | 'NAVIGATE'
  | 'RUN_WHAT_IF';

export type NavigationTarget = 
  | 'OVERVIEW'
  | 'LIVE_PRODUCTION'
  | 'INCIDENT_ANALYSIS'
  | 'RECOVERY_SIMULATOR'
  | 'MAINTENANCE'
  | 'SYSTEM_ACTIVITY';

export type RecoveryAction = 
  | 'NO_ACTION'
  | 'STOP_MAINTAIN'
  | 'DERATE_SPEED'
  | 'REROUTE_WORKLOAD'
  | 'CONTINUE_UNCHECKED';

// Allowed machine IDs based on simulation config M01-M10
export const VALID_MACHINE_IDS = [
  'M01', 'M02', 'M03', 'M04', 'M05', 
  'M06', 'M07', 'M08', 'M09', 'M10'
];

export interface VoiceCommand {
  intent: Intent;
  machine_id?: string;
  target?: NavigationTarget;
  action?: RecoveryAction;
}

export interface CommandResult {
  success: boolean;
  error?: string;
  message?: string;
  command?: VoiceCommand;
}

export class VoiceCommandService {
  static parseAndValidate(rawCommand: any): CommandResult {
    if (!rawCommand || typeof rawCommand !== 'object') {
      return { success: false, error: 'INVALID_FORMAT' };
    }

    const intent = rawCommand.intent as Intent;
    
    switch (intent) {
      case 'GET_CURRENT_STATUS':
      case 'GET_RECOMMENDATION':
        return { success: true, command: { intent } };

      case 'GET_INCIDENT':
        if (!rawCommand.machine_id) {
          return { success: false, error: 'MISSING_MACHINE_ID' };
        }
        if (!VALID_MACHINE_IDS.includes(rawCommand.machine_id)) {
          return { success: false, error: 'INVALID_MACHINE_ID' };
        }
        return { success: true, command: { intent, machine_id: rawCommand.machine_id } };

      case 'NAVIGATE':
        if (!rawCommand.target) {
          return { success: false, error: 'MISSING_TARGET' };
        }
        const validTargets: NavigationTarget[] = [
          'OVERVIEW', 'LIVE_PRODUCTION', 'INCIDENT_ANALYSIS', 
          'RECOVERY_SIMULATOR', 'MAINTENANCE', 'SYSTEM_ACTIVITY'
        ];
        if (!validTargets.includes(rawCommand.target)) {
          return { success: false, error: 'INVALID_TARGET' };
        }
        return { success: true, command: { intent, target: rawCommand.target } };

      case 'RUN_WHAT_IF':
        if (!rawCommand.machine_id) {
          return { success: false, error: 'MISSING_MACHINE_ID' };
        }
        if (!VALID_MACHINE_IDS.includes(rawCommand.machine_id)) {
          return { success: false, error: 'INVALID_MACHINE_ID' };
        }
        if (!rawCommand.action) {
          return { success: false, error: 'MISSING_ACTION' };
        }
        const validActions: RecoveryAction[] = [
          'NO_ACTION', 'STOP_MAINTAIN', 'DERATE_SPEED', 
          'REROUTE_WORKLOAD', 'CONTINUE_UNCHECKED'
        ];
        if (!validActions.includes(rawCommand.action)) {
          return { success: false, error: 'INVALID_ACTION' };
        }
        return { success: true, command: { intent, machine_id: rawCommand.machine_id, action: rawCommand.action } };

      default:
        return { success: false, error: 'UNSUPPORTED_COMMAND' };
    }
  }

  static handleCommand(command: VoiceCommand): any {
    // For now, this is just a stub returning a structured not-implemented response
    // as per STEP 2 constraints.
    return {
      success: true,
      status: "NOT_IMPLEMENTED_YET",
      command
    };
  }
}
