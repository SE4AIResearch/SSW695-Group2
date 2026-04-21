import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Collapse
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { observabilityApi, configApi } from '../services/api';

export default function Issues() {
  const [repositories, setRepositories] = useState([]);
  const [selectedRepoId, setSelectedRepoId] = useState(parseInt(localStorage.getItem('repo_id')) || null);
  const [issues, setIssues] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [expandedRow, setExpandedRow] = useState(null);

  useEffect(() => {
    fetchRepositories();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedRepoId) {
      fetchIssues();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedRepoId, page, rowsPerPage]);

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

  const fetchIssues = async () => {
    setLoading(true);
    setError('');
    try {
      const offset = page * rowsPerPage;
      const response = await observabilityApi.getIssues(selectedRepoId, {
        limit: rowsPerPage,
        offset: offset
      });
      
      console.log('Issues data:', response.data);
      setIssues(response.data.issues || []);
      setTotal(response.data.total || 0);
    } catch (err) {
      console.error('Error loading issues:', err);
      setError('Failed to load issues');
    } finally {
      setLoading(false);
    }
  };

  const handleRepoChange = (event) => {
    const newRepoId = parseInt(event.target.value);
    setSelectedRepoId(newRepoId);
    localStorage.setItem('repo_id', newRepoId);
    setPage(0); // Reset to first page
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleExpandRow = (issueNumber) => {
    setExpandedRow(expandedRow === issueNumber ? null : issueNumber);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const currentRepo = repositories.find(r => r.repo_id === selectedRepoId);

  if (repositories.length === 0 && !loading) {
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
            Issues
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
            
            <IconButton 
              onClick={fetchIssues}
              sx={{ color: '#7C3AED' }}
              title="Refresh"
            >
              <RefreshIcon />
            </IconButton>
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
          Showing issues for <strong>{currentRepo.repo_full_name}</strong> - Total: {total} issues
        </Alert>
      )}

      {/* Issues Table */}
      <Card>
        {loading ? (
          <Box display="flex" justifyContent="center" py={6}>
            <CircularProgress size={60} />
          </Box>
        ) : issues.length === 0 ? (
          <CardContent sx={{ p: 5, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary">
              No issues found for this repository
            </Typography>
          </CardContent>
        ) : (
          <>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ backgroundColor: '#F9FAFB' }}>
                    <TableCell width="50px"></TableCell>
                    <TableCell><strong>Issue #</strong></TableCell>
                    <TableCell><strong>Title</strong></TableCell>
                    <TableCell><strong>Labels</strong></TableCell>
                    <TableCell><strong>Author</strong></TableCell>
                    <TableCell><strong>Created</strong></TableCell>
                    <TableCell><strong>Updated</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {issues.map((issue) => (
                    <React.Fragment key={issue.event_id}>
                      {/* Main Row */}
                      <TableRow 
                        sx={{ 
                          '&:hover': { backgroundColor: '#F9FAFB' },
                          cursor: 'pointer'
                        }}
                        onClick={() => handleExpandRow(issue.issue_number)}
                      >
                        <TableCell>
                          <IconButton size="small">
                            {expandedRow === issue.issue_number ? (
                              <ExpandLessIcon />
                            ) : (
                              <ExpandMoreIcon />
                            )}
                          </IconButton>
                        </TableCell>
                        <TableCell>
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              fontFamily: 'monospace',
                              fontWeight: 600,
                              color: '#7C3AED'
                            }}
                          >
                            #{issue.issue_number}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body1" fontWeight="500">
                            {issue.title}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {issue.labels && issue.labels.length > 0 ? (
                              issue.labels.map((label, idx) => (
                                <Chip
                                  key={idx}
                                  label={label}
                                  size="small"
                                  sx={{ 
                                    backgroundColor: '#EDE9FE', 
                                    color: '#7C3AED',
                                    fontSize: '0.75rem'
                                  }}
                                />
                              ))
                            ) : (
                              <Typography variant="caption" color="text.secondary">
                                No labels
                              </Typography>
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            @{issue.author_login}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption" color="text.secondary">
                            {formatDate(issue.issue_created_at)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption" color="text.secondary">
                            {formatDate(issue.issue_updated_at)}
                          </Typography>
                        </TableCell>
                      </TableRow>

                      {/* Expanded Row - Issue Body */}
                      <TableRow>
                        <TableCell 
                          colSpan={7} 
                          sx={{ 
                            py: 0,
                            borderBottom: expandedRow === issue.issue_number ? 1 : 0 
                          }}
                        >
                          <Collapse 
                            in={expandedRow === issue.issue_number} 
                            timeout="auto" 
                            unmountOnExit
                          >
                            <Box sx={{ p: 3, backgroundColor: '#F9FAFB' }}>
                              <Typography variant="caption" color="text.secondary" fontWeight="bold">
                                Issue Description:
                              </Typography>
                              <Box 
                                sx={{ 
                                  mt: 1, 
                                  p: 2, 
                                  backgroundColor: 'white',
                                  borderRadius: 1,
                                  border: '1px solid #E5E7EB',
                                  maxHeight: 300,
                                  overflow: 'auto'
                                }}
                              >
                                <Typography 
                                  variant="body2" 
                                  sx={{ 
                                    whiteSpace: 'pre-wrap',
                                    fontFamily: 'monospace',
                                    fontSize: '0.875rem'
                                  }}
                                >
                                  {issue.body || 'No description provided'}
                                </Typography>
                              </Box>
                              
                              <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                                <Typography variant="caption" color="text.secondary">
                                  <strong>Event ID:</strong> {issue.event_id}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  <strong>Snapshot:</strong> {formatDate(issue.snapshot_at)}
                                </Typography>
                              </Box>
                            </Box>
                          </Collapse>
                        </TableCell>
                      </TableRow>
                    </React.Fragment>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {/* Pagination */}
            <TablePagination
              component="div"
              count={total}
              page={page}
              onPageChange={handleChangePage}
              rowsPerPage={rowsPerPage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              rowsPerPageOptions={[10, 25, 50, 100]}
            />
          </>
        )}
      </Card>
    </Box>
  );
}