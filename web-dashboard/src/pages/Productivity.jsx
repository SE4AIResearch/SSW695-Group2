import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import { observabilityApi, configApi } from '../services/api';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

export default function Productivity() {
  const [repositories, setRepositories] = useState([]);
  const [selectedRepoId, setSelectedRepoId] = useState(parseInt(localStorage.getItem('repo_id')) || null);
  const [timeWindow, setTimeWindow] = useState('30d');
  const [productivityData, setProductivityData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchRepositories();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedRepoId) {
      fetchProductivity();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedRepoId, timeWindow]);

  const fetchRepositories = async () => {
    try {
      const response = await configApi.getAllRepos({ limit: 100, offset: 0 });
      setRepositories(response.data.repos || []);
      
      if (!selectedRepoId && response.data.repos.length > 0) {
        setSelectedRepoId(response.data.repos[0].repo_id);
      }
    } catch (err) {
      console.error('Error loading repositories:', err);
      setError('Failed to load repositories');
    }
  };

  const fetchProductivity = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await observabilityApi.getProductivity(selectedRepoId, timeWindow);
      console.log('Productivity data:', response.data);
      setProductivityData(response.data);
    } catch (err) {
      console.error('Error loading productivity:', err);
      setError('Failed to load productivity data');
    } finally {
      setLoading(false);
    }
  };

  const handleRepoChange = (event) => {
    const newRepoId = parseInt(event.target.value);
    setSelectedRepoId(newRepoId);
    localStorage.setItem('repo_id', newRepoId);
  };

  const currentRepo = repositories.find(r => r.repo_id === selectedRepoId);

  const getWindowLabel = (window) => {
    const labels = {
      '7d': 'Last 7 Days',
      '30d': 'Last 30 Days',
      '90d': 'Last 90 Days',
      'all': 'All Time'
    };
    return labels[window] || window;
  };

  // Calculate average resolution time safely
  const calculateAvgResolutionTime = () => {
    if (!productivityData || !productivityData.developers || productivityData.developers.length === 0) {
      return '0.0';
    }
    
    const total = productivityData.developers.reduce((sum, dev) => 
      sum + (dev.avg_resolution_hours || 0), 0);
    const avg = total / productivityData.developers.length;
    return avg.toFixed(1);
  };

  if (loading && !productivityData) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (repositories.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <Alert severity="info" sx={{ maxWidth: 500 }}>
          No repositories enrolled yet. Go to <strong>Setup</strong> to enroll your first repository.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h3" fontWeight="600" sx={{ mb: 2 }}>
            Developer Productivity
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            {/* Repository Selector */}
            <FormControl sx={{ minWidth: 300 }}>
              <InputLabel>Repository</InputLabel>
              <Select
                value={selectedRepoId || ''}
                onChange={handleRepoChange}
                label="Repository"
              >
                {repositories.map((repo) => (
                  <MenuItem key={repo.repo_id} value={repo.repo_id}>
                    {repo.repo_full_name} (ID: {repo.repo_id})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Time Window Selector */}
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Time Period</InputLabel>
              <Select
                value={timeWindow}
                onChange={(e) => setTimeWindow(e.target.value)}
                label="Time Period"
              >
                <MenuItem value="7d">Last 7 Days</MenuItem>
                <MenuItem value="30d">Last 30 Days</MenuItem>
                <MenuItem value="90d">Last 90 Days</MenuItem>
                <MenuItem value="all">All Time</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {currentRepo && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Showing productivity for <strong>{currentRepo.repo_full_name}</strong> - {getWindowLabel(timeWindow)}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" py={6}>
          <CircularProgress size={60} />
        </Box>
      ) : productivityData && productivityData.developers ? (
        <>
          {/* Summary Cards */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="caption" color="text.secondary" fontWeight="bold">
                    Total Developers
                  </Typography>
                  <Typography variant="h3" fontWeight="bold" sx={{ mt: 1 }}>
                    {productivityData.developers.length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="caption" color="text.secondary" fontWeight="bold">
                    Total Resolved
                  </Typography>
                  <Typography variant="h3" fontWeight="bold" sx={{ mt: 1, color: '#10B981' }}>
                    {productivityData.developers.reduce((sum, dev) => sum + (dev.resolved_count || 0), 0)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="caption" color="text.secondary" fontWeight="bold">
                    Avg Resolution Time
                  </Typography>
                  <Typography variant="h3" fontWeight="bold" sx={{ mt: 1, color: '#7C3AED' }}>
                    {calculateAvgResolutionTime()}h
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="caption" color="text.secondary" fontWeight="bold">
                    Active Issues
                  </Typography>
                  <Typography variant="h3" fontWeight="bold" sx={{ mt: 1, color: '#F59E0B' }}>
                    {productivityData.developers.reduce((sum, dev) => sum + (dev.open_assignments || 0), 0)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Developer Performance Table */}
          <Card sx={{ mb: 4 }}>
            <CardContent>
              <Typography variant="h5" fontWeight="600" sx={{ mb: 3 }}>
                Developer Performance
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow sx={{ backgroundColor: '#F9FAFB' }}>
                      <TableCell><strong>Developer</strong></TableCell>
                      <TableCell align="right"><strong>Resolved</strong></TableCell>
                      <TableCell align="right"><strong>Avg Resolution Time</strong></TableCell>
                      <TableCell align="right"><strong>Open Issues</strong></TableCell>
                      <TableCell align="right"><strong>Capacity</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {productivityData.developers
                      .sort((a, b) => (b.resolved_count || 0) - (a.resolved_count || 0))
                      .map((dev) => (
                        <TableRow key={dev.github_login}>
                          <TableCell>
                            <Typography variant="body1" fontWeight="600">
                              @{dev.github_login}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Chip 
                              label={dev.resolved_count || 0} 
                              size="small"
                              sx={{ backgroundColor: '#D1FAE5', color: '#065F46', fontWeight: 600 }}
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              {dev.avg_resolution_hours ? dev.avg_resolution_hours.toFixed(1) : '0.0'}h
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              {dev.open_assignments || 0}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={`${dev.open_assignments || 0}/${dev.max_capacity || 0}`}
                              size="small"
                              color={(dev.open_assignments || 0) >= (dev.max_capacity || 0) ? 'error' : 'success'}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>

          {/* Resolution Trend Chart */}
          {productivityData.developers.some(dev => dev.buckets && dev.buckets.length > 0) && (
            <Card>
              <CardContent>
                <Typography variant="h5" fontWeight="600" sx={{ mb: 3 }}>
                  Resolution Trends
                </Typography>
                <ResponsiveContainer width="100%" height={350}>
                  <LineChart
                    data={productivityData.developers[0].buckets.map((bucket, idx) => ({
                      period: bucket.period_start,
                      ...productivityData.developers.reduce((acc, dev) => ({
                        ...acc,
                        [dev.github_login]: dev.buckets && dev.buckets[idx] ? dev.buckets[idx].resolved || 0 : 0
                      }), {})
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    {productivityData.developers.map((dev, idx) => (
                      <Line
                        key={dev.github_login}
                        type="monotone"
                        dataKey={dev.github_login}
                        stroke={`hsl(${idx * 360 / productivityData.developers.length}, 70%, 50%)`}
                        strokeWidth={2}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </>
      ) : (
        <Card>
          <CardContent sx={{ p: 5, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary">
              No productivity data available
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}