import { useState, useCallback } from "react";
import api from "./axios";

/**
 * Unified hook for all reporting and analytics endpoints
 * 
 * Provides access to:
 * - dashboard: Overall system metrics
 * - statusSummary: Task status distribution
 * - slaCompliance: SLA compliance by priority
 * - teamPerformance: User/agent performance metrics
 * - workflowMetrics: Workflow performance analytics
 * - stepPerformance: Step-level performance metrics
 * - departmentAnalytics: Department-level analytics
 * - priorityDistribution: Priority breakdown and metrics
 * - ticketAge: Ticket age/aging analysis
 * - assignmentAnalytics: Task assignment analytics by role
 * - auditActivity: User and system audit activity
 */
const useReportingAnalytics = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // State for each endpoint
  const [dashboard, setDashboard] = useState(null);
  const [statusSummary, setStatusSummary] = useState(null);
  const [slaCompliance, setSlaCompliance] = useState(null);
  const [teamPerformance, setTeamPerformance] = useState(null);
  const [workflowMetrics, setWorkflowMetrics] = useState(null);
  const [stepPerformance, setStepPerformance] = useState(null);
  const [departmentAnalytics, setDepartmentAnalytics] = useState(null);
  const [priorityDistribution, setPriorityDistribution] = useState(null);
  const [ticketAge, setTicketAge] = useState(null);
  const [assignmentAnalytics, setAssignmentAnalytics] = useState(null);
  const [auditActivity, setAuditActivity] = useState(null);

  /**
   * Fetch all analytics endpoints
   */
  const fetchAllAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const endpoints = [
        { name: 'dashboard', url: 'analytics/dashboard/', setter: setDashboard },
        { name: 'statusSummary', url: 'analytics/status-summary/', setter: setStatusSummary },
        { name: 'slaCompliance', url: 'analytics/sla-compliance/', setter: setSlaCompliance },
        { name: 'teamPerformance', url: 'analytics/team-performance/', setter: setTeamPerformance },
        { name: 'workflowMetrics', url: 'analytics/workflow-metrics/', setter: setWorkflowMetrics },
        { name: 'stepPerformance', url: 'analytics/step-performance/', setter: setStepPerformance },
        { name: 'departmentAnalytics', url: 'analytics/department-analytics/', setter: setDepartmentAnalytics },
        { name: 'priorityDistribution', url: 'analytics/priority-distribution/', setter: setPriorityDistribution },
        { name: 'ticketAge', url: 'analytics/ticket-age/', setter: setTicketAge },
        { name: 'assignmentAnalytics', url: 'analytics/assignment-analytics/', setter: setAssignmentAnalytics },
        { name: 'auditActivity', url: 'analytics/audit-activity/', setter: setAuditActivity },
      ];

      // Fetch all endpoints in parallel
      const promises = endpoints.map(({ url, setter }) =>
        api.get(url)
          .then(res => ({ setter, data: res.data }))
          .catch(err => {
            console.error(`Error fetching ${url}:`, err);
            return { setter, data: null, error: err };
          })
      );

      const results = await Promise.all(promises);

      // Update state for each endpoint
      results.forEach(({ setter, data, error: err }) => {
        if (err) {
          setError(`Failed to fetch analytics data: ${err.message}`);
        } else {
          setter(data);
        }
      });

      return results;
    } catch (err) {
      setError(err.message || 'Failed to fetch analytics data');
      console.error('Analytics fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Fetch dashboard metrics
   */
  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('analytics/dashboard/');
      setDashboard(res.data);
      return res.data;
    } catch (err) {
      setError('Failed to fetch dashboard metrics');
      console.error('Dashboard fetch error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Fetch status summary
   */
  const fetchStatusSummary = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('analytics/status-summary/');
      setStatusSummary(res.data);
      return res.data;
    } catch (err) {
      setError('Failed to fetch status summary');
      console.error('Status summary fetch error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Fetch SLA compliance with optional priority filter
   */
  const fetchSlaCompliance = useCallback(async (priority = null) => {
    setLoading(true);
    setError(null);
    try {
      const params = priority ? `?priority=${priority}` : '';
      const res = await api.get(`analytics/sla-compliance/${params}`);
      setSlaCompliance(res.data);
      return res.data;
    } catch (err) {
      setError('Failed to fetch SLA compliance');
      console.error('SLA compliance fetch error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Fetch team performance metrics
   */
  const fetchTeamPerformance = useCallback(async (role = null) => {
    setLoading(true);
    setError(null);
    try {
      const params = role ? `?role=${role}` : '';
      const res = await api.get(`analytics/team-performance/${params}`);
      setTeamPerformance(res.data);
      return res.data;
    } catch (err) {
      setError('Failed to fetch team performance');
      console.error('Team performance fetch error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Fetch workflow metrics with optional filters
   */
  const fetchWorkflowMetrics = useCallback(async (department = null, workflowId = null) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (department) params.append('department', department);
      if (workflowId) params.append('workflow_id', workflowId);
      const queryString = params.toString() ? `?${params.toString()}` : '';
      const res = await api.get(`analytics/workflow-metrics/${queryString}`);
      setWorkflowMetrics(res.data);
      return res.data;
    } catch (err) {
      setError('Failed to fetch workflow metrics');
      console.error('Workflow metrics fetch error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Fetch step performance metrics
   */
  const fetchStepPerformance = useCallback(async (workflowId = null) => {
    setLoading(true);
    setError(null);
    try {
      const params = workflowId ? `?workflow_id=${workflowId}` : '';
      const res = await api.get(`analytics/step-performance/${params}`);
      setStepPerformance(res.data);
      return res.data;
    } catch (err) {
      setError('Failed to fetch step performance');
      console.error('Step performance fetch error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Fetch department analytics
   */
  const fetchDepartmentAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('analytics/department-analytics/');
      setDepartmentAnalytics(res.data);
      return res.data;
    } catch (err) {
      setError('Failed to fetch department analytics');
      console.error('Department analytics fetch error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Fetch priority distribution
   */
  const fetchPriorityDistribution = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('analytics/priority-distribution/');
      setPriorityDistribution(res.data);
      return res.data;
    } catch (err) {
      setError('Failed to fetch priority distribution');
      console.error('Priority distribution fetch error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Fetch ticket age analytics
   */
  const fetchTicketAge = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('analytics/ticket-age/');
      setTicketAge(res.data);
      return res.data;
    } catch (err) {
      setError('Failed to fetch ticket age analytics');
      console.error('Ticket age fetch error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Fetch assignment analytics
   */
  const fetchAssignmentAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('analytics/assignment-analytics/');
      setAssignmentAnalytics(res.data);
      return res.data;
    } catch (err) {
      setError('Failed to fetch assignment analytics');
      console.error('Assignment analytics fetch error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Fetch audit activity
   */
  const fetchAuditActivity = useCallback(async (days = 30) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`analytics/audit-activity/?days=${days}`);
      setAuditActivity(res.data);
      return res.data;
    } catch (err) {
      setError('Failed to fetch audit activity');
      console.error('Audit activity fetch error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    // State
    loading,
    error,
    dashboard,
    statusSummary,
    slaCompliance,
    teamPerformance,
    workflowMetrics,
    stepPerformance,
    departmentAnalytics,
    priorityDistribution,
    ticketAge,
    assignmentAnalytics,
    auditActivity,
    
    // Methods
    fetchAllAnalytics,
    fetchDashboard,
    fetchStatusSummary,
    fetchSlaCompliance,
    fetchTeamPerformance,
    fetchWorkflowMetrics,
    fetchStepPerformance,
    fetchDepartmentAnalytics,
    fetchPriorityDistribution,
    fetchTicketAge,
    fetchAssignmentAnalytics,
    fetchAuditActivity,
  };
};

export default useReportingAnalytics;
