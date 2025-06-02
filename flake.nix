{
  description = "dev shell with uv & claude code";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    # python 3.8.18
    nixpkgs_p38.url = "github:NixOS/nixpkgs/336eda0d07dc5e2be1f923990ad9fdb6bc8e28e3";
  };

  outputs =
    {
      self,
      nixpkgs,
      nixpkgs_p38,
    }:
    let
      system = "x86_64-linux";
      mkDevShell =
        pythonPkg: pkgs:
        pkgs.mkShell {
          buildInputs = with pkgs; [
            nodejs_20
            pythonPkg
            uv
          ];
          shellHook = ''
            export LD_LIBRARY_PATH=${
              pkgs.lib.makeLibraryPath [
                pkgs.zlib
                pkgs.stdenv.cc.cc
              ]
            }:$LD_LIBRARY_PATH
            export NPM_CONFIG_PREFIX="$HOME/.npm-global"
            export PATH="$HOME/.npm-global/bin:$PATH"

            if [ ! -f "$HOME/.npm-global/bin/claude" ]; then
              npm install -g @anthropic-ai/claude-code
            fi
          '';
        };
    in
    {
      devShells.${system} = {
        py38 = mkDevShell (import nixpkgs_p38 { inherit system; }).python38Full (
          import nixpkgs { inherit system; }
        );
        py312 = mkDevShell (import nixpkgs { inherit system; }).python312Full (
          import nixpkgs { inherit system; }
        );
      };
      # default to py312
      devShell.${system} = self.devShells.${system}.py312;
    };
}
