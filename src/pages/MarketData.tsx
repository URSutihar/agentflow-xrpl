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

  // Real RLUSD issuer address from Ripple
  const RLUSD_ISSUER = "rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De"; // Official RLUSD issuer
  
  // Backup USD issuer (Bitstamp USD) as fallback
  const USD_ISSUER = "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B"; // Bitstamp USD

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

      // Try RLUSD first, fallback to USD if not available
      const currencies = [
        { currency: "RLUSD", issuer: RLUSD_ISSUER, name: "RLUSD" },
        { currency: "USD", issuer: USD_ISSUER, name: "USD" }
      ];

      let successfulFetch = false;

      for (const curr of currencies) {
        try {
          // Fetch buy orders (XRP → Currency)
          const buyOrdersRequest = {
            method: "book_offers",
            params: [{
              taker_gets: {
                currency: curr.currency,
                issuer: curr.issuer
              },
              taker_pays: "XRP",
              limit: 20
            }]
          };

          // Fetch sell orders (Currency → XRP)
          const sellOrdersRequest = {
            method: "book_offers", 
            params: [{
              taker_gets: "XRP",
              taker_pays: {
                currency: curr.currency,
                issuer: curr.issuer
              },
              limit: 20
            }]
          };

          // Use multiple XRPL public servers with fallback
          const endpoints = [
            'https://xrplcluster.com/',
            'https://s1.ripple.com:51234/',
            'https://s2.ripple.com:51234/'
          ];

          let buyData, sellData;

          for (const endpoint of endpoints) {
            try {
              const [buyResponse, sellResponse] = await Promise.all([
                fetch(endpoint, {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify(buyOrdersRequest)
                }),
                fetch(endpoint, {
                  method: 'POST', 
                  headers: {
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify(sellOrdersRequest)
                })
              ]);

              if (buyResponse.ok && sellResponse.ok) {
                buyData = await buyResponse.json();
                sellData = await sellResponse.json();
                
                // Check if we got valid responses
                if (buyData?.result && sellData?.result) {
                  setBuyOffers(buyData.result.offers || []);
                  setSellOffers(sellData.result.offers || []);

                  // Calculate current price from best offer
                  if (buyData.result.offers && buyData.result.offers.length > 0) {
                    const bestOffer = buyData.result.offers[0];
                    setCurrentPrice(parseFloat(bestOffer.quality));
                  }

                  successfulFetch = true;
                  console.log(`Successfully fetched ${curr.name} market data from ${endpoint}`);
                  break;
                }
              }
            } catch (endpointError) {
              console.warn(`Failed to fetch from ${endpoint}:`, endpointError);
              continue;
            }
          }

          if (successfulFetch) break;

        } catch (currencyError) {
          console.warn(`Failed to fetch ${curr.name} data:`, currencyError);
          continue;
        }
      }

      if (!successfulFetch) {
        throw new Error('Unable to fetch market data from any source');
      }

    } catch (err) {
      setError('Failed to fetch market data. The XRP Ledger might be experiencing issues or the trading pair may not be available.');
      console.error('Error fetching market data:', err);
      
      // Set empty data on error
      setBuyOffers([]);
      setSellOffers([]);
      setCurrentPrice(null);
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
          <h1>XRP/USD Market Data</h1>
        </div>
        <div className="loading-spinner">Loading market data...</div>
        
        {/* Dock positioned at bottom */}
        <div className="floating-dock">
          <Dock 
            items={dockItems}
            panelHeight={68}
            baseItemSize={50}
            magnification={70}
          />
        </div>
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
          <h1>XRP/USD Market Data</h1>
        </div>
        <div className="error-message">
          {error}
          <button onClick={fetchMarketData} className="retry-button">
            Retry
          </button>
        </div>
        
        {/* Dock positioned at bottom */}
        <div className="floating-dock">
          <Dock 
            items={dockItems}
            panelHeight={68}
            baseItemSize={50}
            magnification={70}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="market-data-page">
      <div className="market-header">
        <button onClick={() => navigate('/')} className="back-button">
          ← Back to Home
        </button>
        <h1>XRP/USD Market Data</h1>
        {currentPrice && (
          <div className="current-price">
            Current Price: {currentPrice.toFixed(6)} USD per XRP
          </div>
        )}
      </div>

      <div className="market-content">
        <div className="order-books">
          {/* Buy Orders (Bids) */}
          <div className="order-book">
            <h2>Buy Orders (Bids)</h2>
            <div className="order-book-header">
              <span>Price (USD/XRP)</span>
              <span>Amount (XRP)</span>
              <span>Total (USD)</span>
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
              <span>Price (USD/XRP)</span>
              <span>Amount (USD)</span>
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
              . It shows real-time order book data for the XRP/USD trading pair.
            </p>
            <button onClick={fetchMarketData} className="refresh-button">
              Refresh Data
            </button>
          </div>
        </div>
      </div>

      {/* Dock positioned at bottom */}
      <div className="floating-dock">
        <Dock 
          items={dockItems}
          panelHeight={68}
          baseItemSize={50}
          magnification={70}
        />
      </div>
    </div>
  );
};

export default MarketData;