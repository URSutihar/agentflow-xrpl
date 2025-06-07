import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { VscHome, VscArchive, VscCode, VscGraph } from 'react-icons/vsc';
import { FiSun, FiMoon, FiUsers } from 'react-icons/fi';
import Dock from '../components/Dock';
import type { DockItemData } from '../components/Dock';
import { useTheme } from '../hooks/useTheme';
import './MarketData.css';

interface Offer {
  Account: string;
  TakerGets: {
    currency?: string;
    issuer?: string;
    value?: string;
  } | string;
  TakerPays: {
    currency?: string;
    issuer?: string;
    value?: string;
  } | string;
  quality: string;
  owner_funds?: string;
}

interface BookOffersResponse {
  result: {
    offers: Offer[];
    ledger_current_index?: number;
  };
}

const MarketData: React.FC = () => {
  const [buyOffers, setBuyOffers] = useState<Offer[]>([]);
  const [sellOffers, setSellOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const navigate = useNavigate();
  const { isDarkMode, toggleTheme } = useTheme();

  // RLUSD issuer address (you may need to update this with the actual RLUSD issuer)
  const RLUSD_ISSUER = "rLUSDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"; // Replace with actual RLUSD issuer

  const dockItems: DockItemData[] = [
    { 
      icon: <VscHome size={18} />, 
      label: 'Home', 
      onClick: () => navigate('/') 
    },
    { 
      icon: <VscCode size={18} />, 
      label: 'Workflow Builder', 
      onClick: () => navigate('/workflow-builder') 
    },
    { 
      icon: <VscGraph size={18} />, 
      label: 'Market Data', 
      onClick: () => navigate('/market-data') 
    },
    { 
      icon: <VscArchive size={18} />, 
      label: 'Projects', 
      onClick: () => navigate('/projects') 
    },
    { 
      icon: <FiUsers size={18} />, 
      label: 'Team', 
      onClick: () => navigate('/team') 
    },
    // Separator
    { 
      icon: null, 
      label: '', 
      onClick: () => {},
      isSeparator: true
    },
    { 
      icon: isDarkMode ? <FiMoon size={18} /> : <FiSun size={18} />, 
      label: isDarkMode ? 'Light Mode' : 'Dark Mode', 
      onClick: toggleTheme 
    },
  ];

  const fetchMarketData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch buy orders (XRP → RLUSD)
      const buyOrdersRequest = {
        method: "book_offers",
        params: [{
          taker_gets: {
            currency: "RLUSD",
            issuer: RLUSD_ISSUER
          },
          taker_pays: {
            currency: "XRP"
          },
          limit: 20
        }]
      };

      // Fetch sell orders (RLUSD → XRP)
      const sellOrdersRequest = {
        method: "book_offers",
        params: [{
          taker_gets: {
            currency: "XRP"
          },
          taker_pays: {
            currency: "RLUSD",
            issuer: RLUSD_ISSUER
          },
          limit: 20
        }]
      };

      // Make parallel API calls to XRPL public servers
      const [buyResponse, sellResponse] = await Promise.all([
        fetch('https://xrplcluster.com/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(buyOrdersRequest)
        }),
        fetch('https://xrplcluster.com/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(sellOrdersRequest)
        })
      ]);

      const buyData: BookOffersResponse = await buyResponse.json();
      const sellData: BookOffersResponse = await sellResponse.json();

      setBuyOffers(buyData.result.offers || []);
      setSellOffers(sellData.result.offers || []);

      // Calculate current price from best offer
      if (buyData.result.offers && buyData.result.offers.length > 0) {
        const bestOffer = buyData.result.offers[0];
        setCurrentPrice(parseFloat(bestOffer.quality));
      }

    } catch (err) {
      setError('Failed to fetch market data. Please try again.');
      console.error('Error fetching market data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMarketData();
    // Refresh data every 30 seconds
    const interval = setInterval(fetchMarketData, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (amount: any, currency: string) => {
    if (currency === 'XRP') {
      // XRP is in drops, convert to XRP
      return (parseInt(amount) / 1000000).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 6
      });
    } else {
      // Other currencies are already in decimal format
      return parseFloat(amount).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 6
      });
    }
  };

  const getCurrency = (currencyObj: any) => {
    if (typeof currencyObj === 'string') {
      return 'XRP';
    }
    return currencyObj.currency || 'XRP';
  };

  const getAmount = (currencyObj: any) => {
    if (typeof currencyObj === 'string') {
      return currencyObj;
    }
    return currencyObj.value || '0';
  };

  if (loading) {
    return (
      <div className="market-data-page">
        <div className="market-header">
          <button onClick={() => navigate('/')} className="back-button">
            ← Back to Home
          </button>
          <h1>XRP/RLUSD Market Data</h1>
        </div>
        <div className="loading-spinner">Loading market data...</div>
        
        {/* Dock positioned at bottom */}
        <Dock 
          items={dockItems}
          panelHeight={68}
          baseItemSize={50}
          magnification={70}
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="market-data-page">
        <div className="market-header">
          <button onClick={() => navigate('/')} className="back-button">
            ← Back to Home
          </button>
          <h1>XRP/RLUSD Market Data</h1>
        </div>
        <div className="error-message">
          {error}
          <button onClick={fetchMarketData} className="retry-button">
            Retry
          </button>
        </div>
        
        {/* Dock positioned at bottom */}
        <Dock 
          items={dockItems}
          panelHeight={68}
          baseItemSize={50}
          magnification={70}
        />
      </div>
    );
  }

  return (
    <div className="market-data-page">
      <div className="market-header">
        <button onClick={() => navigate('/')} className="back-button">
          ← Back to Home
        </button>
        <h1>XRP/RLUSD Market Data</h1>
        {currentPrice && (
          <div className="current-price">
            Current Price: {currentPrice.toFixed(6)} RLUSD per XRP
          </div>
        )}
      </div>

      <div className="market-content">
        <div className="order-books">
          {/* Buy Orders (Bids) */}
          <div className="order-book">
            <h2>Buy Orders (Bids)</h2>
            <div className="order-book-header">
              <span>Price (RLUSD/XRP)</span>
              <span>Amount (XRP)</span>
              <span>Total (RLUSD)</span>
            </div>
            <div className="order-book-body">
              {buyOffers.length > 0 ? (
                buyOffers.map((offer, index) => (
                  <div key={index} className="order-row buy-order">
                    <span>{parseFloat(offer.quality).toFixed(6)}</span>
                    <span>{formatCurrency(getAmount(offer.TakerPays), getCurrency(offer.TakerPays))}</span>
                    <span>{formatCurrency(getAmount(offer.TakerGets), getCurrency(offer.TakerGets))}</span>
                  </div>
                ))
              ) : (
                <div className="no-orders">No buy orders available</div>
              )}
            </div>
          </div>

          {/* Sell Orders (Asks) */}
          <div className="order-book">
            <h2>Sell Orders (Asks)</h2>
            <div className="order-book-header">
              <span>Price (RLUSD/XRP)</span>
              <span>Amount (RLUSD)</span>
              <span>Total (XRP)</span>
            </div>
            <div className="order-book-body">
              {sellOffers.length > 0 ? (
                sellOffers.map((offer, index) => (
                  <div key={index} className="order-row sell-order">
                    <span>{(1 / parseFloat(offer.quality)).toFixed(6)}</span>
                    <span>{formatCurrency(getAmount(offer.TakerPays), getCurrency(offer.TakerPays))}</span>
                    <span>{formatCurrency(getAmount(offer.TakerGets), getCurrency(offer.TakerGets))}</span>
                  </div>
                ))
              ) : (
                <div className="no-orders">No sell orders available</div>
              )}
            </div>
          </div>
        </div>

        <div className="market-info">
          <div className="info-card">
            <h3>Market Statistics</h3>
            <div className="stat-item">
              <span>Total Buy Orders:</span>
              <span>{buyOffers.length}</span>
            </div>
            <div className="stat-item">
              <span>Total Sell Orders:</span>
              <span>{sellOffers.length}</span>
            </div>
            <div className="stat-item">
              <span>Last Updated:</span>
              <span>{new Date().toLocaleTimeString()}</span>
            </div>
          </div>

          <div className="info-card">
            <h3>About This Data</h3>
            <p>
              This market data is fetched directly from the XRP Ledger using the{' '}
              <a 
                href="https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/path-and-order-book-methods/book_offers"
                target="_blank"
                rel="noopener noreferrer"
              >
                book_offers API
              </a>
              . It shows real-time order book data for the XRP/RLUSD trading pair.
            </p>
            <button onClick={fetchMarketData} className="refresh-button">
              Refresh Data
            </button>
          </div>
        </div>
      </div>

      {/* Dock positioned at bottom */}
      <Dock 
        items={dockItems}
        panelHeight={68}
        baseItemSize={50}
        magnification={70}
      />
    </div>
  );
};

export default MarketData;