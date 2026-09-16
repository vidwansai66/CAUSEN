import { VoiceCommandService } from './VoiceCommandService';

function runTests() {
  let passed = 0;
  let failed = 0;

  function assert(condition: boolean, name: string) {
    if (condition) {
      console.log(`✅ PASS: ${name}`);
      passed++;
    } else {
      console.error(`❌ FAIL: ${name}`);
      failed++;
    }
  }

  // 1. Valid GET_CURRENT_STATUS command.
  const res1 = VoiceCommandService.parseAndValidate({ intent: 'GET_CURRENT_STATUS' });
  assert(res1.success === true && res1.command?.intent === 'GET_CURRENT_STATUS', 'Valid GET_CURRENT_STATUS');

  // 2. Valid GET_INCIDENT with a real configured machine ID.
  const res2 = VoiceCommandService.parseAndValidate({ intent: 'GET_INCIDENT', machine_id: 'M03' });
  assert(res2.success === true && res2.command?.machine_id === 'M03', 'Valid GET_INCIDENT with M03');

  // 3. Valid NAVIGATE command.
  const res3 = VoiceCommandService.parseAndValidate({ intent: 'NAVIGATE', target: 'INCIDENT_ANALYSIS' });
  assert(res3.success === true && res3.command?.target === 'INCIDENT_ANALYSIS', 'Valid NAVIGATE command');

  // 4. Invalid NAVIGATE target rejected.
  const res4 = VoiceCommandService.parseAndValidate({ intent: 'NAVIGATE', target: 'RANDOM_PAGE' });
  assert(res4.success === false && res4.error === 'INVALID_TARGET', 'Invalid NAVIGATE target rejected');

  // 5. Valid RUN_WHAT_IF action.
  const res5 = VoiceCommandService.parseAndValidate({ intent: 'RUN_WHAT_IF', machine_id: 'M03', action: 'DERATE_SPEED' });
  assert(res5.success === true && res5.command?.action === 'DERATE_SPEED', 'Valid RUN_WHAT_IF action');

  // 6. Invalid recovery action rejected.
  const res6 = VoiceCommandService.parseAndValidate({ intent: 'RUN_WHAT_IF', machine_id: 'M03', action: 'EXPLODE_FACTORY' });
  assert(res6.success === false && res6.error === 'INVALID_ACTION', 'Invalid recovery action rejected');

  // 7. Missing machine ID rejected where required.
  const res7 = VoiceCommandService.parseAndValidate({ intent: 'GET_INCIDENT' });
  assert(res7.success === false && res7.error === 'MISSING_MACHINE_ID', 'Missing machine ID rejected');

  const res7b = VoiceCommandService.parseAndValidate({ intent: 'RUN_WHAT_IF', action: 'DERATE_SPEED' });
  assert(res7b.success === false && res7b.error === 'MISSING_MACHINE_ID', 'Missing machine ID rejected for RUN_WHAT_IF');

  // 8. Arbitrary route/API input cannot be passed through.
  const res8 = VoiceCommandService.parseAndValidate({ intent: 'DELETE_DATABASE' });
  assert(res8.success === false && res8.error === 'UNSUPPORTED_COMMAND', 'Arbitrary input unsupported intent rejected');

  console.log(`\nTests completed: ${passed} passed, ${failed} failed.`);
  if (failed > 0) {
    throw new Error('Tests failed');
  }
}

runTests();
