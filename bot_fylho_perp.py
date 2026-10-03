#... garde tout jusqu'à la partie achat...

        if rsi<RSI_SEUIL and sym not in memory:
            try:
                ex_fut.set_leverage(LEVERAGE, sym_fut, params={'side': 'BOTH'})
            except:
                try:
                    ex_fut.set_leverage(LEVERAGE, sym_fut, params={'side': 'LONG'})
                    ex_fut.set_leverage(LEVERAGE, sym_fut, params={'side': 'SHORT'})
                except: pass

            qty=(AMOUNT_USDT*LEVERAGE)/price
            sl_price=price*(1-SL_PCT/100)
            tp_price=price*(1+TRAILING_PCT/100) # TP initial 5%

            ex_fut.create_market_buy_order(sym_fut, qty)

            # --- SL REEL SUR BINGX ---
            try:
                ex_fut.create_order(sym_fut, 'stopMarket', 'sell', qty, None, params={'stopPrice': sl_price})
            except Exception as e:
                send_tg(f"⚠️ SL non posé {sym}: {e}")

            # --- TP REEL SUR BINGX ---
            try:
                ex_fut.create_order(sym_fut, 'takeProfitMarket', 'sell', qty, None, params={'stopPrice': tp_price})
            except:
                try:
                    ex_fut.create_order(sym_fut, 'limit', 'sell', qty, tp_price)
                except Exception as e:
                    send_tg(f"⚠️ TP non posé {sym}: {e}")

            memory[sym]={'entry':price,'high':price,'sl':sl_price,'tp':tp_price,'be_done':False,'qty':qty}
            save_mem(memory)
            send_tg(f"🚀 LONG REEL {sym} x{LEVERAGE} entry {price:.4f} RSI {rsi:.1f} | SL {sl_price:.4f} (-{SL_PCT}%) TP {tp_price:.4f} (+{TRAILING_PCT}%)")