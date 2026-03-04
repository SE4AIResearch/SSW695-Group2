import React, { useState } from 'react';
import { 
  Grid, 
  Paper, 
  Typography, 
  Box, 
  Card,
  CardContent,
  Button,
  Select,
  MenuItem,
  FormControl,
  TextField,
  InputAdornment,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import { 
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';
import SearchIcon from '@mui/icons-material/Search';
import BugReportIcon from '@mui/icons-material/BugReport';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import SpeedIcon from '@mui/icons-material/Speed';
import AccessTimeIcon from '@mui/icons-material/AccessTime';

// Sample data for bug trends
const bugTrendData = [
  { date: '2025-01-02', bugs: 12 },
  { date: '2025-01-03', bugs: 18 },
  { date: '2025-01-04', bugs: 15 },
  { date: '2025-01-05', bugs: 22 },
  { date: '2025-01-06', bugs: 19 },
  { date: '2025-01-07', bugs: 25 },
  { date: '2025-01-08', bugs: 20 },
];

// Sample data for category breakdown
const categoryData = [
  { name: 'Frontend', value: 45, color: '#7C3AED' },
  { name: 'Backend', value: 30, color: '#3B82F6' },
  { name: 'Database', value: 15, color: '#10B981' },
  { name: 'API', value: 10, color: '#F59E0B' },
];

// Sample data for recent activity
const recentActivity = [
  { id: '#234', title: 'Login page crashes on Safari', assignee: 'sarah_dev', category: 'Frontend', priority: 'High', time: '2 mins ago' },
  { id: '#233', title: 'API timeout on user endpoint', assignee: 'john_backend', category: 'Backend', priority: 'Critical', time: '5 mins ago' },
  { id: '#232', title: 'UI button alignment issue', assignee: 'emma_dev', category: 'Frontend', priority: 'Low', time: '10 mins ago' },
  { id: '#231', title: 'Database query slow performance', assignee: 'john_backend', category: 'Database', priority: 'Medium', time: '15 mins ago' },
];

// Priority colors
const getPriorityColor = (priority) => {
  switch (priority) {
    case 'Critical': return '#EF4444';
    case 'High': return '#F97316';
    case 'Medium': return '#F59E0B';
    case 'Low': return '#10B981';
    default: return '#6B7280';
  }
};

export default function Dashboard() {
  const [timePeriod, setTimePeriod] = useState('Last 7 Days');
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <Box sx={{ width: '100%' }}>
      {/* Page Title - Bigger */}
      <Typography variant="h3" gutterBottom fontWeight="600" sx={{ mb: 3 }}>
        Dashboard
      </Typography>

      {/* Search Bar - Bigger */}
      <Box sx={{ mb: 4, display: 'flex', gap: 2 }}>
        <TextField
          fullWidth
          placeholder="Search by bug ID, title, or assignee..."
          variant="outlined"
          size="medium"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ fontSize: 24 }} />
              </InputAdornment>
            ),
          }}
          sx={{ 
            backgroundColor: 'white',
            '& .MuiInputBase-input': {
              fontSize: '1rem',
              py: 1.5
            }
          }}
        />
        <Button 
          variant="contained" 
          size="large"
          sx={{ 
            px: 5,
            py: 1.5,
            fontSize: '1rem',
            backgroundColor: '#7C3AED',
            textTransform: 'none',
            fontWeight: 600,
            '&:hover': {
              backgroundColor: '#6D28D9'
            }
          }}
        >
          SEARCH
        </Button>
      </Box>

      {/* Stats Cards - Bigger */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 1, fontSize: '0.875rem' }}>
                    Total Bugs
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                    145
                  </Typography>
                  <Typography variant="body2" color="success.main" sx={{ fontSize: '0.875rem' }}>
                    +12% from last week
                  </Typography>
                </Box>
                <Box
                  sx={{
                    backgroundColor: '#EDE9FE',
                    borderRadius: '50%',
                    p: 2.5,
                    display: 'flex',
                  }}
                >
                  <BugReportIcon sx={{ color: '#7C3AED', fontSize: 36 }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 1, fontSize: '0.875rem' }}>
                    Auto-Triaged
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                    132
                  </Typography>
                  <Typography variant="body2" color="success.main" sx={{ fontSize: '0.875rem' }}>
                    91% success rate
                  </Typography>
                </Box>
                <Box
                  sx={{
                    backgroundColor: '#D1FAE5',
                    borderRadius: '50%',
                    p: 2.5,
                    display: 'flex',
                  }}
                >
                  <CheckCircleIcon sx={{ color: '#10B981', fontSize: 36 }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 1, fontSize: '0.875rem' }}>
                    Accuracy
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                    87%
                  </Typography>
                  <Typography variant="body2" color="success.main" sx={{ fontSize: '0.875rem' }}>
                    +3% improvement
                  </Typography>
                </Box>
                <Box
                  sx={{
                    backgroundColor: '#DBEAFE',
                    borderRadius: '50%',
                    p: 2.5,
                    display: 'flex',
                  }}
                >
                  <SpeedIcon sx={{ color: '#3B82F6', fontSize: 36 }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 1, fontSize: '0.875rem' }}>
                    Avg Time Saved
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                    8 min
                  </Typography>
                  <Typography variant="body2" color="success.main" sx={{ fontSize: '0.875rem' }}>
                    Per bug triaged
                  </Typography>
                </Box>
                <Box
                  sx={{
                    backgroundColor: '#FEF3C7',
                    borderRadius: '50%',
                    p: 2.5,
                    display: 'flex',
                  }}
                >
                  <AccessTimeIcon sx={{ color: '#F59E0B', fontSize: 36 }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Bug Trends Chart - Bigger */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h5" sx={{ color: '#7C3AED', fontWeight: 'bold' }}>
                  Bug Triaging Trends
                </Typography>
                <FormControl size="medium">
                  <Select
                    value={timePeriod}
                    onChange={(e) => setTimePeriod(e.target.value)}
                    sx={{ minWidth: 160 }}
                  >
                    <MenuItem value="Last 7 Days">Last 7 Days</MenuItem>
                    <MenuItem value="Last 30 Days">Last 30 Days</MenuItem>
                    <MenuItem value="Last 90 Days">Last 90 Days</MenuItem>
                  </Select>
                </FormControl>
              </Box>

              {/* Area Chart - Bigger */}
              <ResponsiveContainer width="100%" height={350}>
                <AreaChart data={bugTrendData}>
                  <defs>
                    <linearGradient id="colorBugs" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#7C3AED" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 13 }}
                    tickFormatter={(value) => value.slice(5)}
                  />
                  <YAxis tick={{ fontSize: 13 }} />
                  <Tooltip 
                    contentStyle={{ fontSize: '14px' }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="bugs" 
                    stroke="#7C3AED" 
                    strokeWidth={3}
                    fillOpacity={1} 
                    fill="url(#colorBugs)" 
                  />
                </AreaChart>
              </ResponsiveContainer>

              <Box sx={{ textAlign: 'center', mt: 3 }}>
                <Typography variant="h2" fontWeight="bold" sx={{ color: '#7C3AED' }}>
                  131
                </Typography>
                <Typography variant="h6" color="text.secondary" sx={{ mt: 1 }}>
                  Bugs Triaged This Week
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Category Breakdown - Bigger */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h5" sx={{ color: '#7C3AED', fontWeight: 'bold', mb: 3 }}>
                Category Breakdown
              </Typography>

              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    innerRadius={70}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ fontSize: '14px' }} />
                </PieChart>
              </ResponsiveContainer>

              <Box sx={{ mt: 3 }}>
                {categoryData.map((category) => (
                  <Box 
                    key={category.name} 
                    sx={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      mb: 2
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <Box
                        sx={{
                          width: 14,
                          height: 14,
                          borderRadius: '50%',
                          backgroundColor: category.color
                        }}
                      />
                      <Typography variant="body1" sx={{ fontSize: '1rem' }}>
                        {category.name}
                      </Typography>
                    </Box>
                    <Typography variant="body1" fontWeight="bold" sx={{ fontSize: '1rem' }}>
                      {category.value}%
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity - Bigger */}
        <Grid item xs={12}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h5" sx={{ color: '#7C3AED', fontWeight: 'bold', mb: 3 }}>
                Recent Activity
              </Typography>

              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontSize: '1rem', fontWeight: 'bold' }}>Bug ID</TableCell>
                      <TableCell sx={{ fontSize: '1rem', fontWeight: 'bold' }}>Title</TableCell>
                      <TableCell sx={{ fontSize: '1rem', fontWeight: 'bold' }}>Category</TableCell>
                      <TableCell sx={{ fontSize: '1rem', fontWeight: 'bold' }}>Priority</TableCell>
                      <TableCell sx={{ fontSize: '1rem', fontWeight: 'bold' }}>Assigned To</TableCell>
                      <TableCell sx={{ fontSize: '1rem', fontWeight: 'bold' }}>Time</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {recentActivity.map((bug) => (
                      <TableRow key={bug.id} hover sx={{ '& td': { py: 2 } }}>
                        <TableCell>
                          <Typography variant="body1" fontWeight="600" sx={{ color: '#7C3AED', fontSize: '0.95rem' }}>
                            {bug.id}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body1" sx={{ fontSize: '0.95rem' }}>
                            {bug.title}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={bug.category} 
                            size="medium"
                            sx={{ 
                              backgroundColor: '#EDE9FE',
                              color: '#7C3AED',
                              fontSize: '0.875rem',
                              fontWeight: 500
                            }}
                          />
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={bug.priority} 
                            size="medium"
                            sx={{ 
                              backgroundColor: getPriorityColor(bug.priority) + '20',
                              color: getPriorityColor(bug.priority),
                              fontWeight: 'bold',
                              fontSize: '0.875rem'
                            }}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body1" sx={{ fontSize: '0.95rem' }}>
                            @{bug.assignee}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
                            {bug.time}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              <Box sx={{ mt: 3, textAlign: 'center' }}>
                <Button 
                  variant="outlined" 
                  size="large"
                  sx={{ 
                    textTransform: 'none',
                    fontSize: '1rem',
                    px: 4,
                    py: 1.5,
                    borderColor: '#7C3AED',
                    color: '#7C3AED',
                    fontWeight: 600,
                    '&:hover': {
                      borderColor: '#6D28D9',
                      backgroundColor: '#F3F4F6'
                    }
                  }}
                >
                  View All Activity
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}