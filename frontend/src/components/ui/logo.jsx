// noinspection JSValidateTypes,JSUnusedGlobalSymbols

import React from 'react';
import { Link } from 'react-router-dom';
import logoImage from '@/assets/images/logo-h-116.png';

export const Logo = ({ className = '' }) => {
  return (
    <Link to="/" className={`flex items-center ${className}`}>
      <img
        src={logoImage}
        alt="Panama In Context"
        className="h-16 w-auto"
      />
    </Link>
  );
};