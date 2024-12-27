import React from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { Users, Layers, BookOpen, PenTool, Image, Share2, Globe2, Menu, LogOut } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Logo } from '@/components/ui/logo';
import { cn } from '@/lib/utils';


// Navigation configuration
const navItems = [
  {
    title: 'Users',
    icon: Users,
    href: '/users'
  },
  {
    title: 'Content Manager',
    icon: Layers,
    href: '/content',
    subItems: [
      { title: 'Taxonomies & Categories', href: '/content/taxonomies' },
      { title: 'Tags', href: '/content/tags' },
      { title: 'Article Suggestions', href: '/content/suggestions' }
    ]
  },
  {
    title: 'Researcher',
    icon: BookOpen,
    href: '/research'
  },
  {
    title: 'Writer',
    icon: PenTool,
    href: '/writer'
  },
  {
    title: 'Media Manager',
    icon: Image,
    href: '/media',
    subItems: [
      { title: 'Media Suggestions', href: '/media/suggestions' },
      { title: 'Media Candidates', href: '/media/candidates' },
      { title: 'Media Library', href: '/media/library' }
    ]
  },
  {
    title: 'Social Media',
    icon: Share2,
    href: '/social',
    subItems: [
      { title: 'Accounts', href: '/social/accounts' },
      { title: 'Posts', href: '/social/posts' },
      { title: 'Hashtag Groups', href: '/social/hashtags' }
    ]
  },
  {
    title: 'Translations',
    icon: Globe2,
    href: '/translations'
  }
];

const NavLink = ({ href, children, className }) => {
  const location = useLocation();
  const isActive = location.pathname === href;

  return (
    <Link to={href}>
      <Button
        variant={isActive ? "secondary" : "ghost"}
        className={cn("w-full justify-start", className)}
      >
        {children}
      </Button>
    </Link>
  );
};

const AdminLayout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = React.useState(true);
  const [expandedItem, setExpandedItem] = React.useState(null);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  // Update expanded item based on current path
  React.useEffect(() => {
    const currentPath = location.pathname;
    const expandedIndex = navItems.findIndex(item =>
      item.subItems?.some(subItem => currentPath.startsWith(subItem.href))
    );
    setExpandedItem(expandedIndex >= 0 ? expandedIndex : null);
  }, [location.pathname]);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile Header */}
      <div className="xl:hidden flex items-center justify-between p-4 border-b">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            <Menu className="h-6 w-6"/>
          </Button>
        </div>
      </div>

      {/* Sidebar */}
      <aside className={cn(
        "fixed left-0 top-0 z-40 h-screen w-64 transform transition-transform duration-200 ease-in-out bg-background border-r",
        sidebarOpen ? "translate-x-0" : "-translate-x-full",
        "hidden lg:block xl:translate-x-0"
      )}>
        {/* Logo Area */}
        <div className="h-32 flex items-center justify-center border-b">
          <Logo className="h-32 flex items-center justify-center" />
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2">
          {navItems.map((item, index) => (
            <div key={index} className="space-y-1">
              {item.subItems ? (
                <>
                  <Button
                    variant="ghost"
                    className="w-full justify-start"
                    onClick={() => setExpandedItem(expandedItem === index ? null : index)}
                  >
                    <item.icon className="mr-2 h-4 w-4"/>
                    {item.title}
                  </Button>
                  {expandedItem === index && (
                    <div className="ml-6 space-y-1">
                      {item.subItems.map((subItem, subIndex) => (
                        <NavLink
                          key={subIndex}
                          href={subItem.href}
                          className="text-sm font-normal"
                        >
                          {subItem.title}
                        </NavLink>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <NavLink href={item.href}>
                  <item.icon className="mr-2 h-4 w-4"/>
                  {item.title}
                </NavLink>
              )}
            </div>
          ))}
          {/* Logout section at bottom */}
          <div className="p-4 border-t">
            <Button
              variant="ghost"
              className="w-full justify-start text-red-600 hover:text-red-600 hover:bg-red-100"
              onClick={handleLogout}
            >
              <LogOut className="mr-2 h-4 w-4"/>
              Logout
            </Button>
          </div>
        </nav>
      </aside>

      {/* Main Content */}
      <main className={cn(
        "transition-all duration-200 ease-in-out",
        sidebarOpen ? "lg:ml-64" : "lg:ml-0",
        "p-4 lg:p-8"
      )}>
        <div className="max-w-full">
          <Outlet/>
        </div>
      </main>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 xl:hidden z-30"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};

export default AdminLayout;