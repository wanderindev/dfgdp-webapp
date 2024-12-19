import React from 'react';
import { Users, Layers, BookOpen, PenTool, Image, Share2, Globe2, Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

// Navigation items configuration
const navItems = [
  {
    title: 'Users',
    icon: Users,
    href: '/admin/users'
  },
  {
    title: 'Content Manager',
    icon: Layers,
    href: '/admin/content',
    subItems: [
      { title: 'Taxonomies & Categories', href: '/admin/content/taxonomies' },
      { title: 'Tags', href: '/admin/content/tags' },
      { title: 'Article Suggestions', href: '/admin/content/suggestions' }
    ]
  },
  {
    title: 'Researcher',
    icon: BookOpen,
    href: '/admin/research'
  },
  {
    title: 'Writer',
    icon: PenTool,
    href: '/admin/writer'
  },
  {
    title: 'Media Manager',
    icon: Image,
    href: '/admin/media'
  },
  {
    title: 'Social Media',
    icon: Share2,
    href: '/admin/social',
    subItems: [
      { title: 'Accounts', href: '/admin/social/accounts' },
      { title: 'Posts', href: '/admin/social/posts' },
      { title: 'Hashtag Groups', href: '/admin/social/hashtags' }
    ]
  },
  {
    title: 'Translations',
    icon: Globe2,
    href: '/admin/translations'
  }
];

const AdminLayout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = React.useState(true);
  const [expandedItem, setExpandedItem] = React.useState(null);

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile Header */}
      <div className="lg:hidden flex items-center justify-between p-4 border-b">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            <Menu className="h-6 w-6" />
          </Button>
          <span className="font-semibold text-lg">Panama In Context</span>
        </div>
      </div>

      {/* Sidebar */}
      <aside className={cn(
        "fixed left-0 top-0 z-40 h-screen w-64 transform transition-transform duration-200 ease-in-out bg-background border-r",
        sidebarOpen ? "translate-x-0" : "-translate-x-full",
        "lg:translate-x-0" // Always visible on large screens
      )}>
        {/* Logo Area */}
        <div className="h-16 flex items-center justify-center border-b">
          <span className="font-semibold text-lg">Panama In Context</span>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2">
          {navItems.map((item, index) => (
            <div key={index} className="space-y-1">
              <Button
                variant="ghost"
                className="w-full justify-start"
                onClick={() => setExpandedItem(expandedItem === index ? null : index)}
              >
                <item.icon className="mr-2 h-4 w-4" />
                {item.title}
              </Button>
              {item.subItems && expandedItem === index && (
                <div className="ml-6 space-y-1">
                  {item.subItems.map((subItem, subIndex) => (
                    <Button
                      key={subIndex}
                      variant="ghost"
                      size="sm"
                      className="w-full justify-start text-sm font-normal"
                    >
                      {subItem.title}
                    </Button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main className={cn(
        "transition-all duration-200 ease-in-out",
        sidebarOpen ? "lg:ml-64" : "lg:ml-0",
        "p-4 lg:p-8"
      )}>
        <div className="max-w-7xl mx-auto">
          {children}
        </div>
      </main>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 lg:hidden z-30"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};

export default AdminLayout;