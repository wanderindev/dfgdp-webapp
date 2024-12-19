import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

export const DashboardPage = () => (
  <div className="space-y-4">
    <h1 className="text-2xl font-bold">Dashboard</h1>
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Card>
        <CardHeader>
          <CardTitle>Overview</CardTitle>
        </CardHeader>
        <CardContent>Welcome to the admin dashboard</CardContent>
      </Card>
    </div>
  </div>
);