// @ts-nocheck
import { useState, useCallback, useEffect } from 'react';
import { IngestionState, SourceType, SyncFrequency, JobStatus } from '../types';
import { api } from '@/lib/api';

const INITIAL_STATE: IngestionState = {
  step: 1, sourceType: null, connectionId: null, headers: [], previewRows: [],
  mapping: {}, syncConfig: { frequency: 'daily', agentId: '', conflictResolution: 'overwrite' },
  jobId: null, accountId: null, isProcessing: false, error: null
};

export function useIngestionWizard() {
  const [state, setState] = useState<IngestionState>(INITIAL_STATE);

  // Auto-fetch the default agent "Yanua"
  useEffect(() => {
    const loadDefaultAgent = async () => {
      try {
        const res = await api.get('/agents');
        const agents = res.data.agents || res.data;
        const yanua = agents.find((a: any) => a.nombre.toLowerCase().includes('yanua'));
        if (yanua) {
          updateState({ 
            syncConfig: { ...state.syncConfig, agentId: yanua.id } 
          });
        } else if (agents.length > 0) {
          updateState({ 
            syncConfig: { ...state.syncConfig, agentId: agents[0].id } 
          });
        }
      } catch (err) {
        console.error('Error fetching agents:', err);
      }
    };
    loadDefaultAgent();
  }, []);

  const updateState = useCallback((partial: Partial<IngestionState> & { accountId?: string | null }) => {
    setState(prev => ({ ...prev, ...partial }));
  }, []);

  const nextStep = () => setState(prev => ({ ...prev, step: Math.min(prev.step + 1, 6) }));
  const prevStep = () => setState(prev => ({ ...prev, step: Math.max(prev.step - 1, 1) }));

  const fetchPreview = async (sourceId: string, accountType: string) => {
    setState(prev => ({ ...prev, isProcessing: true, error: null }));
    try {
      const res = await api.post('/oauth/sources/preview', {
        source_id: sourceId, 
        source_type: accountType 
      });
      const data = res.data;
      updateState({ headers: data.headers, previewRows: data.preview_rows, connectionId: sourceId });
    } catch (err: any) {
      updateState({ error: err.message || 'Error al obtener preview' });
    } finally {
      updateState({ isProcessing: false });
    }
  };

  const startSync = async () => {
    setState(prev => ({ ...prev, isProcessing: true, error: null }));
    try {
      const res = await api.post('/sync/sheets', {
        source_id: state.connectionId,
        account_id: state.accountId || 'local',
        column_mapping: state.mapping,
        sync_frequency: state.syncConfig.frequency,
        agent_id: state.syncConfig.agentId
      });
      const { job_id } = res.data;
      updateState({ jobId: job_id, step: 5 }); // Salta a Processing
    } catch (err: any) {
      updateState({ error: err.message || 'Error al iniciar sincronización', isProcessing: false });
    }
  };

  const pollJobStatus = async (): Promise<JobStatus | null> => {
    if (!state.jobId) return null;
    try {
      const res = await api.get(`/sync/jobs/${state.jobId}/status`);
      return res.data;
    } catch (err) {
      return null;
    }
  };

  const resetWizard = () => setState(INITIAL_STATE);

  const handleLocalUpload = async (file: File) => {
    setState(prev => ({ ...prev, isProcessing: true, error: null }));
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const res = await api.post('/upload/parse', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const data = res.data;
      updateState({ 
        headers: data.headers, 
        previewRows: data.preview_rows, 
        connectionId: `local_${file.name}`,
        accountId: 'local',
        isProcessing: false 
      });
      nextStep(); // Avanza automáticamente a Mapeo
    } catch (err: any) {
      updateState({ 
        error: err.response?.data?.detail || err.message || 'Error al procesar archivo', 
        isProcessing: false 
      });
    }
  };

  return { state, updateState, nextStep, prevStep, fetchPreview, startSync, pollJobStatus, resetWizard, handleLocalUpload };
}
