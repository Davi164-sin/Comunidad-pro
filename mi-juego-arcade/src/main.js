import Phaser from "phaser";

const config = {
    type: Phaser.AUTO,
    parent: 'game-container',
    physics: {
        default: 'arcade',
        arcade: { gravity: { y: 900 }, debug: false }
    },
    scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH
    },
    input: { activePointers: 3 },
    scene: { preload, create, update }
};

const game = new Phaser.Game(config);

const WORLD_WIDTH = 3000;
const TOTAL_COINS = 10;

let player, cursors, wasd, platforms, coins, enemies, scoreText, winText, bgGraphics, levelText;
let touchLeft = false, touchRight = false, touchJump = false, touchAction = false;
let score = 0, gameWon = false;
let jumpParticles, bulletGroup;
let currentMiniGame = 1;

// Global game state bridge with HTML UI
window.loadGameLevel = function(lvl) {
    if (player && player.scene) {
        player.scene.scene.restart();
    }
};

window.loadArcadeGame = function(gameId) {
    currentMiniGame = gameId;
    if (player && player.scene) {
        player.scene.scene.restart();
    }
};

function createProceduralTextures(scene) {
    const g = scene.add.graphics();

    // Pixel for particles
    g.fillStyle(0xffffff, 1);
    g.fillRect(0, 0, 4, 4);
    g.generateTexture('pixel', 4, 4);
    g.clear();

    // Suelo
    g.fillStyle(0x2d3748, 1);
    g.fillRect(0, 0, 400, 32);
    g.lineStyle(2, 0x4a5568, 1);
    g.strokeRect(0, 0, 400, 32);
    g.generateTexture('ground', 400, 32);
    g.clear();

    // Jugador (Color dinámico según estado global o nivel)
    const playerColor = window.parent.gameState ? window.parent.gameState.color : 0x00ff00;
    g.fillStyle(playerColor, 1);
    g.fillRoundedRect(0, 0, 32, 48, 8);
    g.fillStyle(0xffffff, 0.5);
    g.fillRoundedRect(4, 4, 12, 12, 6);
    g.generateTexture('player', 32, 48);
    g.clear();

    // Enemigo 1: Hormiga (Ant)
    g.fillStyle(0x8B4513, 1);
    g.fillEllipse(16, 16, 24, 14);
    g.fillStyle(0x000000, 1);
    g.fillCircle(24, 12, 3);
    g.generateTexture('ant', 32, 32);
    g.clear();

    // Enemigo 2: Cucaracha (Roach)
    g.fillStyle(0x5c4033, 1);
    g.fillEllipse(16, 16, 28, 18);
    g.fillStyle(0x3a2820, 1);
    g.fillRect(8, 8, 16, 10);
    g.generateTexture('roach', 32, 32);
    g.clear();

    // Enemigo 3: Ratón (Mouse)
    g.fillStyle(0xa0aec0, 1);
    g.fillCircle(14, 16, 10);
    g.fillCircle(6, 10, 6); // Oreja
    g.generateTexture('mouse', 32, 32);
    g.clear();

    // Enemigo 4: Gusano (Worm)
    g.fillStyle(0xed64a6, 1);
    for(let i=0; i<4; i++) {
        g.fillCircle(8 + i*6, 16, 6);
    }
    g.generateTexture('worm', 32, 32);
    g.clear();

    // Moneda (Coin)
    g.fillStyle(0xffd700, 1);
    g.fillCircle(10, 10, 10);
    g.fillStyle(0xffffff, 0.6);
    g.fillCircle(7, 7, 4);
    g.generateTexture('coin', 20, 20);
    g.clear();

    // Proyectil Láser / Insecticida
    g.fillStyle(0x00ffff, 1);
    g.fillCircle(6, 6, 6);
    g.generateTexture('bullet', 12, 12);
    g.clear();
}

function drawBackground(scene, width, height) {
    if (bgGraphics) bgGraphics.destroy();
    bgGraphics = scene.add.graphics();
    bgGraphics.fillGradientStyle(0x0f172a, 0x0f172a, 0x1e1b4b, 0x1e1b4b, 1);
    bgGraphics.fillRect(0, 0, width, height);
    bgGraphics.setScrollFactor(0).setDepth(-1);
}

function preload() {
    createProceduralTextures(this);
}

function create() {
    drawBackground(this, this.cameras.main.width, this.cameras.main.height);
    this.physics.world.setBounds(0, 0, WORLD_WIDTH, 600);

    jumpParticles = this.add.particles('pixel').createEmitter({
        speed: 120,
        scale: { start: 1, end: 0 },
        blendMode: 'ADD',
        active: false,
        lifespan: 350
    });

    bulletGroup = this.physics.add.group({ allowGravity: false });

    platforms = this.physics.add.staticGroup();
    for (let x = 0; x < WORLD_WIDTH; x += 400) {
        platforms.create(x + 200, 580, 'ground').refreshBody();
    }
    
    // Plataformas flotantes variadas según el mini-juego o nivel
    const plats = [
        [300, 450], [550, 350], [800, 260], [1100, 400], 
        [1400, 300], [1700, 440], [2000, 320], [2300, 250], [2600, 400]
    ];
    plats.forEach(p => platforms.create(p[0], p[1], 'ground').refreshBody());

    // JUGADOR
    player = this.physics.add.sprite(100, 450, 'player');
    player.setCollideWorldBounds(true);
    this.physics.add.collider(player, platforms);

    // MONEDAS
    coins = this.physics.add.group({ allowGravity: false });
    plats.forEach((p, idx) => {
        if (idx < TOTAL_COINS) {
            coins.create(p[0], p[1] - 40, 'coin').body.setImmovable(true);
        }
    });
    this.physics.add.overlap(player, coins, collectCoin, null, this);

    // ENEMIGOS (Bichos: hormigas, cucarachas, ratones, gusanos)
    enemies = this.physics.add.group({ allowGravity: false });
    const enemyTypes = ['ant', 'roach', 'mouse', 'worm'];
    plats.forEach((p, idx) => {
        if (idx % 2 === 0 && idx < 8) {
            const type = enemyTypes[idx % enemyTypes.length];
            const enemy = enemies.create(p[0], p[1] - 25, type);
            enemy.startX = p[0];
            enemy.range = 70;
            enemy.direction = 1;
            enemy.speed = 70 + idx * 5;
        }
    });
    this.physics.add.overlap(player, enemies, hitEnemy, null, this);
    this.physics.add.overlap(bulletGroup, enemies, hitEnemyWithBullet, null, this);

    scoreText = this.add.text(16, 50, 'Monedas: 0 / ' + TOTAL_COINS, { fontSize: '22px', color: '#ffffff', backgroundColor: '#000000aa', padding: {x:8, y:4} }).setScrollFactor(0).setDepth(100);
    levelText = this.add.text(16, 90, 'Modo / Nivel: ' + currentMiniGame, { fontSize: '18px', color: '#38bdf8', backgroundColor: '#000000aa', padding: {x:8, y:4} }).setScrollFactor(0).setDepth(100);
    winText = this.add.text(400, 300, '¡Nivel Superado! 🎉', { fontSize: '42px', color: '#ffd700', backgroundColor: '#000000cc', padding: {x:20, y:10} }).setScrollFactor(0).setDepth(200).setOrigin(0.5).setVisible(false);

    this.cameras.main.setBounds(0, 0, WORLD_WIDTH, 600);
    this.cameras.main.startFollow(player, true, 0.1, 0.1);

    cursors = this.input.keyboard.createCursorKeys();
    wasd = this.input.keyboard.addKeys('W,A,S,D,SPACE,F');
    createTouchControls(this);
}

let jumpCount = 0;
function update() {
    if (gameWon) return;
    const speed = 220, jumpForce = -450;
    const onGround = player.body.blocked.down || player.body.touching.down;

    if (onGround) jumpCount = 0;

    if (cursors.left.isDown || wasd.A.isDown || touchLeft) player.body.setVelocityX(-speed);
    else if (cursors.right.isDown || wasd.D.isDown || touchRight) player.body.setVelocityX(speed);
    else player.body.setVelocityX(0);

    // Salto normal o Doble Salto (comprado en tienda)
    const hasDoubleJump = window.parent.gameState && window.parent.gameState.items.doubleJump;
    const jumpPressed = Phaser.Input.Keyboard.JustDown(cursors.up) || Phaser.Input.Keyboard.JustDown(wasd.W) || Phaser.Input.Keyboard.JustDown(wasd.SPACE) || touchJump;

    if (jumpPressed) {
        if (onGround) {
            player.body.setVelocityY(jumpForce);
            jumpParticles.explode(12, player.x, player.y + 24);
            touchJump = false;
        } else if (hasDoubleJump && jumpCount < 1) {
            player.body.setVelocityY(jumpForce * 0.9);
            jumpParticles.explode(15, player.x, player.y);
            jumpCount++;
            touchJump = false;
        }
    }

    // Disparar arma láser (si se compró en tienda)
    const hasLaser = window.parent.gameState && window.parent.gameState.items.laserGun;
    const shootPressed = Phaser.Input.Keyboard.JustDown(wasd.F) || touchAction;
    if (hasLaser && shootPressed) {
        shootBullet(player);
        touchAction = false;
    }

    if (player.y > 650) respawnPlayer();

    enemies.getChildren().forEach(enemy => {
        enemy.x += enemy.speed * enemy.direction * (1 / 60);
        if (enemy.x > enemy.startX + enemy.range) enemy.direction = -1;
        else if (enemy.x < enemy.startX - enemy.range) enemy.direction = 1;
    });

    bulletGroup.getChildren().forEach(bullet => {
        if (bullet.x > player.x + 800 || bullet.x < player.x - 800) bullet.destroy();
    });
}

function shootBullet(p) {
    const bullet = bulletGroup.create(p.x + 20, p.y, 'bullet');
    bullet.body.setVelocityX(500);
}

function collectCoin(p, c) {
    c.destroy();
    score++;
    scoreText.setText('Monedas: ' + score + ' / ' + TOTAL_COINS);
    
    // Sincronizar monedas con UI global
    if (window.parent.gameState) {
        window.parent.gameState.coins++;
        window.parent.updateHUDValues();
    }

    this.add.particles('pixel').createEmitter({
        x: c.x, y: c.y, speed: 60, scale: { start: 1, end: 0 }, lifespan: 400
    }).explode(12);
    
    if (score >= TOTAL_COINS) winGame();
}

function hitEnemy(p, e) {
    const hasShield = window.parent.gameState && window.parent.gameState.items.shield;
    if (p.body.velocity.y > 0 && p.y + 24 <= e.y - 10) {
        e.destroy();
        p.body.setVelocityY(-350);
        this.cameras.main.shake(100, 0.01);
    } else if (hasShield) {
        // Escudo protege una vez
        window.parent.gameState.items.shield = false;
        e.destroy();
        this.cameras.main.shake(150, 0.015);
        alert('¡Escudo antibichos destruyó al enemigo!');
    } else {
        respawnPlayer();
        this.cameras.main.shake(200, 0.02);
    }
}

function hitEnemyWithBullet(bullet, enemy) {
    bullet.destroy();
    enemy.destroy();
    this.cameras.main.shake(80, 0.01);
}

function respawnPlayer() {
    player.setPosition(100, 450);
    player.body.setVelocity(0, 0);
}

function winGame() {
    gameWon = true;
    player.body.setVelocity(0, 0);
    winText.setVisible(true);
}

function createTouchControls(scene) {
    const createBtn = (x, y, text) => {
        let btn = scene.add.circle(x, y, 38, 0x4f46e5, 0.6).setInteractive().setScrollFactor(0).setDepth(100);
        scene.add.text(x, y, text, { fontSize: '32px', color: '#fff' }).setOrigin(0.5).setScrollFactor(0).setDepth(101);
        return btn;
    };

    const leftBtn = createBtn(70, 520, '◀');
    const rightBtn = createBtn(160, 520, '▶');
    const jumpBtn = createBtn(720, 520, '▲');
    const actionBtn = createBtn(630, 520, '🔫');

    const press = (btn) => btn.setFillStyle(0x6366f1, 0.9);
    const release = (btn) => btn.setFillStyle(0x4f46e5, 0.6);

    leftBtn.on('pointerdown', () => { touchLeft = true; press(leftBtn); });
    leftBtn.on('pointerup', () => { touchLeft = false; release(leftBtn); });
    
    rightBtn.on('pointerdown', () => { touchRight = true; press(rightBtn); });
    rightBtn.on('pointerup', () => { touchRight = false; release(rightBtn); });

    jumpBtn.on('pointerdown', () => { touchJump = true; press(jumpBtn); });
    jumpBtn.on('pointerup', () => { touchJump = false; release(jumpBtn); });

    actionBtn.on('pointerdown', () => { touchAction = true; press(actionBtn); });
    actionBtn.on('pointerup', () => { touchAction = false; release(actionBtn); });
}
