import React from 'react';
import { 
  Box, 
  Drawer, 
  AppBar, 
  Toolbar, 
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText, 
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Avatar
} from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import PeopleIcon from '@mui/icons-material/People';
import { useNavigate, Outlet, useLocation } from 'react-router-dom';
import { authService } from '../../services/auth';

const drawerWidth = 260; // Increased from 200 to 260

const menuItems = [
  { text: 'Home', icon: <HomeIcon />, path: '/dashboard' },
  { text: 'People', icon: <PeopleIcon />, path: '/team' },
];

export default function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [anchorEl, setAnchorEl] = React.useState(null);
  const user = authService.getCurrentUser();

  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Top Header */}
      <AppBar 
        position="fixed" 
        elevation={0}
        sx={{ 
          zIndex: (theme) => theme.zIndex.drawer + 1,
          backgroundColor: 'white',
          borderBottom: '1px solid #e0e0e0'
        }}
      >
        <Toolbar sx={{ py: 1 }}>
          <Typography 
            variant="h5" 
            sx={{ 
              color: '#7C3AED',
              fontWeight: 'bold',
              mr: 3,
              fontSize: '1.5rem'
            }}
          >
            Buma
          </Typography>

          <Box sx={{ flexGrow: 1 }} />

          {/* User Menu */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="body1" fontWeight="600" sx={{ color: '#333' }}>
                Max
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                Email
              </Typography>
            </Box>
            <IconButton onClick={handleMenu}>
              <Avatar 
                sx={{ 
                  width: 44, 
                  height: 44,
                  backgroundColor: '#7C3AED',
                  fontWeight: 'bold',
                  fontSize: '1.1rem'
                }}
              >
                M
              </Avatar>
            </IconButton>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleClose}
            >
              <MenuItem onClick={handleLogout}>Logout</MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Sidebar - Bigger */}
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            backgroundColor: '#f8f9fa',
            borderRight: '1px solid #e0e0e0',
            overflowX: 'hidden',
          },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto', mt: 3, px: 2 }}>
          <List>
            {menuItems.map((item) => (
              <ListItem 
                button 
                key={item.text}
                onClick={() => navigate(item.path)}
                sx={{
                  borderRadius: 2,
                  mb: 1,
                  py: 1.5,
                  backgroundColor: location.pathname === item.path ? '#7C3AED' : 'transparent',
                  color: location.pathname === item.path ? 'white' : '#666',
                  '&:hover': {
                    backgroundColor: location.pathname === item.path ? '#7C3AED' : '#e0e0e0',
                  }
                }}
              >
                <ListItemIcon sx={{ 
                  color: 'inherit',
                  minWidth: 48
                }}>
                  {React.cloneElement(item.icon, { sx: { fontSize: 26 } })}
                </ListItemIcon>
                <ListItemText 
                  primary={item.text}
                  primaryTypographyProps={{
                    fontSize: '1.05rem',
                    fontWeight: location.pathname === item.path ? 600 : 500
                  }}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      {/* Main Content - Full Screen */}
      <Box 
        component="main" 
        sx={{ 
          flexGrow: 1,
          backgroundColor: '#f5f5f5',
          height: '100vh',
          overflow: 'auto',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        <Toolbar />
        <Box sx={{ 
          flexGrow: 1,
          p: 3,
          width: '100%',
          maxWidth: '100%',
          margin: '0 auto'
        }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}