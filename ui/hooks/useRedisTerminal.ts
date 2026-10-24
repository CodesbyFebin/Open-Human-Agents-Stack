import { useCallback } from 'react';

type Options = {
  sessionIdentity: string;
  podIdentity: string;
  authToken: string;
};

/** Safe placeholder: never claim a live PTY connection without a verified backend. */
export function useRedisTerminal(_options: Options) {
  const transmitTerminalInput = useCallback((_input: string) => {
    throw new Error('Terminal transport is not configured');
  }, []);
  return {
    connectionState: 'DISCONNECTED' as const,
    terminalBufferOutput: '',
    transmitTerminalInput,
  };
}
